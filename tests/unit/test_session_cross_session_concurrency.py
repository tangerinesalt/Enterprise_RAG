import threading
import time
from pathlib import Path

from app.modules.session import session_manager as sm
from app.modules.session.session_manager import SessionManager


class _FakeCollection:
    def count(self) -> int:
        return 1


class _FakeClient:
    def get_collection(self, _name: str) -> _FakeCollection:
        return _FakeCollection()


class _FakeVectorStore:
    def __init__(self, chroma_collection):
        self.chroma_collection = chroma_collection


class _FakeResponse:
    def __init__(self, answer: str = "ok"):
        self.answer = answer
        self.source_nodes = []

    def __str__(self) -> str:
        return self.answer


class _FakeReranker:
    def __init__(self, model: str, top_n: int):
        self.model = model
        self.top_n = top_n


def _make_manager(tmp_path: Path, monkeypatch) -> SessionManager:
    monkeypatch.setattr(sm, "SESSION_ROOT", str(tmp_path / "sessions"))
    return SessionManager()


def _patch_chat_dependencies(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(sm._kb, "exists", lambda _name: True)
    monkeypatch.setattr(sm._kb, "vector_db_path", lambda _name: str(tmp_path / "vector-db"))
    monkeypatch.setattr(sm.chromadb, "PersistentClient", lambda path: _FakeClient())
    monkeypatch.setattr(sm, "_ensure_models_initialized", lambda: False)
    monkeypatch.setattr(sm, "ChromaVectorStore", _FakeVectorStore)
    monkeypatch.setattr(sm.VectorStoreIndex, "from_vector_store", staticmethod(lambda vector_store: object()))
    monkeypatch.setattr(sm, "build_retriever", lambda index, kb_name, top_k, mode: object())


def test_different_sessions_chat_do_not_block_each_other(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    _patch_chat_dependencies(tmp_path, monkeypatch)
    monkeypatch.setattr(sm, "_get_reranker", lambda top_n: object())

    entered_a = threading.Event()
    allow_a = threading.Event()
    b_finished = threading.Event()
    errors: list[Exception] = []

    class _Engine:
        def query(self, query: str):
            if query == "q-a":
                entered_a.set()
                allow_a.wait(1)
            return _FakeResponse(answer=f"answer-{query}")

    class _FakeQueryEngine:
        @staticmethod
        def from_args(**kwargs):
            return _Engine()

    monkeypatch.setattr(sm, "RetrieverQueryEngine", _FakeQueryEngine)

    for session_name in ("a", "b"):
        manager.create(session_name)
        manager.bind(session_name, "kb")

    def run_a():
        try:
            manager.chat("a", "q-a")
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    def run_b():
        try:
            manager.chat("b", "q-b")
            b_finished.set()
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    thread_a = threading.Thread(target=run_a, name="session-a")
    thread_b = threading.Thread(target=run_b, name="session-b")

    thread_a.start()
    assert entered_a.wait(1), "session a did not enter query stage"

    thread_b.start()
    assert b_finished.wait(0.5), "session b was blocked by unrelated session a"

    allow_a.set()
    thread_a.join()
    thread_b.join()

    assert errors == []


def test_different_sessions_can_race_on_shared_reranker_top_n(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    _patch_chat_dependencies(tmp_path, monkeypatch)
    monkeypatch.setattr(sm, "SentenceTransformerRerank", _FakeReranker)
    sm._reranker_instances = {}

    a_entered_query = threading.Event()
    b_finished_query = threading.Event()
    allow_a_finish = threading.Event()
    observed_top_n: dict[str, int] = {}
    errors: list[Exception] = []

    class _Engine:
        def __init__(self, reranker):
            self.reranker = reranker

        def query(self, query: str):
            if query == "q-a":
                a_entered_query.set()
                b_finished_query.wait(1)
                observed_top_n["a"] = self.reranker.top_n
                allow_a_finish.wait(1)
                return _FakeResponse(answer="answer-a")

            observed_top_n["b"] = self.reranker.top_n
            b_finished_query.set()
            return _FakeResponse(answer="answer-b")

    class _FakeQueryEngine:
        @staticmethod
        def from_args(*, node_postprocessors, **kwargs):
            return _Engine(node_postprocessors[0])

    monkeypatch.setattr(sm, "RetrieverQueryEngine", _FakeQueryEngine)

    manager.create("a")
    manager.bind("a", "kb")
    manager.update_config("a", top_n=1)

    manager.create("b")
    manager.bind("b", "kb")
    manager.update_config("b", top_n=9)

    def run_a():
        try:
            manager.chat("a", "q-a")
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    def run_b():
        try:
            manager.chat("b", "q-b")
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    thread_a = threading.Thread(target=run_a, name="session-a")
    thread_b = threading.Thread(target=run_b, name="session-b")

    thread_a.start()
    assert a_entered_query.wait(1), "session a did not reach query stage"

    thread_b.start()
    thread_b.join()

    allow_a_finish.set()
    thread_a.join()

    assert errors == []
    assert observed_top_n["b"] == 9
    assert observed_top_n["a"] == 1


def test_many_sessions_keep_their_own_top_n_under_concurrent_chat(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    _patch_chat_dependencies(tmp_path, monkeypatch)
    monkeypatch.setattr(sm, "SentenceTransformerRerank", _FakeReranker)
    sm._reranker_instances = {}

    session_names = ["s1", "s2", "s3", "s4", "s5", "s6"]
    top_n_by_session = {name: index for index, name in enumerate(session_names, start=1)}
    observed_top_n: dict[str, int] = {}
    errors: list[Exception] = []
    start_barrier = threading.Barrier(len(session_names))

    class _Engine:
        def __init__(self, reranker, session_name: str):
            self.reranker = reranker
            self.session_name = session_name

        def query(self, query: str):
            start_barrier.wait(timeout=1)
            observed_top_n[self.session_name] = self.reranker.top_n
            return _FakeResponse(answer=f"answer-{self.session_name}")

    class _FakeQueryEngine:
        @staticmethod
        def from_args(*, node_postprocessors, retriever, **kwargs):
            return _Engine(node_postprocessors[0], retriever.session_name)

    class _FakeRetriever:
        def __init__(self, session_name: str):
            self.session_name = session_name

    class _FakeStore:
        def add_message(self, *args, **kwargs):
            return None

        def persist(self, *args, **kwargs):
            return None

    monkeypatch.setattr(sm, "RetrieverQueryEngine", _FakeQueryEngine)
    monkeypatch.setattr(sm, "build_retriever", lambda index, kb_name, top_k, mode: _FakeRetriever(kb_name))
    monkeypatch.setattr(
        manager,
        "_prepare_chat_turn",
        lambda name, query, chat_file=None: (
            {"kb_name": name, "top_k": 8, "top_n": top_n_by_session[name], "retriever_mode": "hybrid", "system_prompt": ""},
            f"{name}.json",
            str(tmp_path / f"{name}.json"),
            _FakeStore(),
        ),
    )

    for session_name in session_names:
        manager.create(session_name)

    threads = []
    for session_name in session_names:
        def run_chat(current=session_name):
            try:
                manager.chat(current, f"q-{current}")
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        thread = threading.Thread(
            target=run_chat,
            name=f"thread-{session_name}",
        )
        threads.append(thread)

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert observed_top_n == top_n_by_session


def test_same_top_n_concurrent_lookup_creates_single_reranker_instance(monkeypatch):
    created: list[_FakeReranker] = []
    results: list[_FakeReranker] = []
    errors: list[Exception] = []

    def fake_ctor(model: str, top_n: int):
        time.sleep(0.05)
        reranker = _FakeReranker(model=model, top_n=top_n)
        created.append(reranker)
        return reranker

    monkeypatch.setattr(sm, "SentenceTransformerRerank", fake_ctor)
    sm._reranker_instances = {}

    def run_lookup():
        try:
            results.append(sm._get_reranker(top_n=5))
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    threads = [threading.Thread(target=run_lookup, name=f"lookup-{index}") for index in range(8)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    assert len(created) == 1
    assert len({id(item) for item in results}) == 1

import threading
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
    monkeypatch.setattr(sm, "_get_reranker", lambda top_n: object())


def test_same_session_different_chat_files_do_not_block_each_other(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    _patch_chat_dependencies(tmp_path, monkeypatch)

    entered_chat_a = threading.Event()
    allow_chat_a = threading.Event()
    chat_b_finished = threading.Event()
    errors: list[Exception] = []

    class _Engine:
        def query(self, query: str):
            if query == "q-a":
                entered_chat_a.set()
                allow_chat_a.wait(1)
            return _FakeResponse(answer=f"answer-{query}")

    class _FakeQueryEngine:
        @staticmethod
        def from_args(**kwargs):
            return _Engine()

    monkeypatch.setattr(sm, "RetrieverQueryEngine", _FakeQueryEngine)

    manager.create("demo")
    manager.bind("demo", "kb")
    chat_a = manager.new_chat("demo")
    chat_b = manager.new_chat("demo")

    def run_chat_a():
        try:
            manager.chat("demo", "q-a", chat_a)
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    def run_chat_b():
        try:
            manager.chat("demo", "q-b", chat_b)
            chat_b_finished.set()
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    thread_a = threading.Thread(target=run_chat_a, name="chat-a")
    thread_b = threading.Thread(target=run_chat_b, name="chat-b")

    thread_a.start()
    assert entered_chat_a.wait(1), "chat_a did not enter query stage"

    thread_b.start()
    assert chat_b_finished.wait(0.5), "different chat files in same session were blocked"

    allow_chat_a.set()
    thread_a.join()
    thread_b.join()

    assert errors == []
    assert [m["content"] for m in manager.get_messages("demo", chat_a)] == ["q-a", "answer-q-a"]
    assert [m["content"] for m in manager.get_messages("demo", chat_b)] == ["q-b", "answer-q-b"]


def test_same_session_same_chat_file_remains_serialized(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    _patch_chat_dependencies(tmp_path, monkeypatch)

    entered_first = threading.Event()
    allow_first = threading.Event()
    second_finished = threading.Event()
    errors: list[Exception] = []

    class _Engine:
        def query(self, query: str):
            if query == "q-1":
                entered_first.set()
                allow_first.wait(1)
            return _FakeResponse(answer=f"answer-{query}")

    class _FakeQueryEngine:
        @staticmethod
        def from_args(**kwargs):
            return _Engine()

    monkeypatch.setattr(sm, "RetrieverQueryEngine", _FakeQueryEngine)

    manager.create("demo")
    manager.bind("demo", "kb")
    chat_file = manager.new_chat("demo")

    def run_first():
        try:
            manager.chat("demo", "q-1", chat_file)
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    def run_second():
        try:
            manager.chat("demo", "q-2", chat_file)
            second_finished.set()
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    thread_first = threading.Thread(target=run_first, name="first-chat")
    thread_second = threading.Thread(target=run_second, name="second-chat")

    thread_first.start()
    assert entered_first.wait(1), "first chat did not enter query stage"

    thread_second.start()
    assert not second_finished.wait(0.3), "same chat file unexpectedly ran concurrently"

    allow_first.set()
    thread_first.join()
    thread_second.join()

    assert errors == []
    messages = manager.get_messages("demo", chat_file)
    assert [(m["role"], m["content"]) for m in messages] == [
        ("user", "q-1"),
        ("assistant", "answer-q-1"),
        ("user", "q-2"),
        ("assistant", "answer-q-2"),
    ]


def test_explicit_chat_file_is_stable_while_unrelated_config_updates(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    _patch_chat_dependencies(tmp_path, monkeypatch)

    entered_chat_a = threading.Event()
    allow_chat_a = threading.Event()
    config_updated = threading.Event()
    errors: list[Exception] = []

    class _Engine:
        def query(self, query: str):
            if query == "q-a":
                entered_chat_a.set()
                allow_chat_a.wait(1)
            return _FakeResponse(answer=f"answer-{query}")

    class _FakeQueryEngine:
        @staticmethod
        def from_args(**kwargs):
            return _Engine()

    monkeypatch.setattr(sm, "RetrieverQueryEngine", _FakeQueryEngine)

    manager.create("demo")
    manager.bind("demo", "kb")
    chat_a = manager.new_chat("demo")
    chat_b = manager.new_chat("demo")

    def run_chat_a():
        try:
            manager.chat("demo", "q-a", chat_a)
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    def update_config():
        try:
            manager.update_config("demo", top_k=42)
            config_updated.set()
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    worker = threading.Thread(target=run_chat_a, name="chat-a")
    updater = threading.Thread(target=update_config, name="config-updater")
    worker.start()
    assert entered_chat_a.wait(1), "chat_a did not enter query stage"

    updater.start()
    assert config_updated.wait(0.5), "config update was blocked by unrelated explicit chat"
    allow_chat_a.set()
    worker.join()
    updater.join()

    assert errors == []
    assert manager.get_config("demo")["top_k"] == 42
    assert [m["content"] for m in manager.get_messages("demo", chat_a)] == ["q-a", "answer-q-a"]
    assert manager.get_messages("demo", chat_b) == []

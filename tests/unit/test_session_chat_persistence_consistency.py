from pathlib import Path

from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.storage.chat_store import SimpleChatStore

from app.modules.session import session_manager as sm
from app.modules.session.session_manager import SessionManager


class _FakeCollection:
    def count(self) -> int:
        return 1


class _FakeClient:
    def __init__(self, collection):
        self._collection = collection

    def get_collection(self, _name: str):
        return self._collection


class _FakeVectorStore:
    def __init__(self, chroma_collection):
        self._collection = chroma_collection


class _FakeIndex:
    def __init__(self, vector_store=None):
        self.vector_store = vector_store

    @classmethod
    def from_vector_store(cls, vector_store):
        return cls(vector_store=vector_store)


class _FakeNode:
    def __init__(self, text: str, score: float):
        self.text = text
        self.score = score


class _FakeResponse:
    def __init__(self, answer: str, tokens: list[str]):
        self._answer = answer
        self.response_gen = iter(tokens)
        self.source_nodes = [_FakeNode("source one", 0.91), _FakeNode("source two", 0.77)]

    def __str__(self) -> str:
        return self._answer


class _FakeQueryEngine:
    def __init__(self, response):
        self._response = response

    def query(self, _query: str):
        return self._response


def _make_manager(tmp_path: Path, monkeypatch) -> SessionManager:
    monkeypatch.setattr(sm, "SESSION_ROOT", str(tmp_path / "sessions"))
    monkeypatch.setattr(sm._kb, "exists", lambda _name: True)
    monkeypatch.setattr(sm._kb, "vector_db_path", lambda _name: str(tmp_path / "vector-db"))
    monkeypatch.setattr(sm.chromadb, "PersistentClient", lambda path: _FakeClient(_FakeCollection()))
    monkeypatch.setattr(sm, "_ensure_models_initialized", lambda: False)
    monkeypatch.setattr(sm, "ChromaVectorStore", _FakeVectorStore)
    monkeypatch.setattr(sm, "VectorStoreIndex", _FakeIndex)
    monkeypatch.setattr(sm, "build_retriever", lambda *args, **kwargs: object())
    monkeypatch.setattr(sm, "_get_reranker", lambda top_n=5: object())
    monkeypatch.setattr(sm, "SimilarityPostprocessor", lambda similarity_cutoff=0.1: object())
    monkeypatch.setattr(SessionManager, "_build_retrieval_hint", lambda self, sources, top_k, top_n: "")

    def fake_from_args(*args, streaming=False, **kwargs):
        if streaming:
            return _FakeQueryEngine(_FakeResponse("stream answer", ["stream ", "answer"]))
        return _FakeQueryEngine(_FakeResponse("sync answer", []))

    monkeypatch.setattr(sm.RetrieverQueryEngine, "from_args", fake_from_args)
    return SessionManager()


def test_sync_chat_persists_structured_sources_without_inline_suffix(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.create("demo")
    manager.bind("demo", "kb1")
    chat_file = manager.new_chat("demo")

    result = manager.chat("demo", "hello", chat_file)

    assert result["answer"] == "sync answer"
    assert result["sources"] == [
        {"text": "source one", "score": 0.91},
        {"text": "source two", "score": 0.77},
    ]

    messages = manager.get_messages("demo", chat_file)
    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["content"] == "sync answer"
    assert messages[-1]["additional_kwargs"] == {
        "sources": [
            {"text": "source one", "score": 0.91},
            {"text": "source two", "score": 0.77},
        ]
    }


def test_stream_chat_persists_same_assistant_message_shape_as_sync_chat(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.create("demo")
    manager.bind("demo", "kb1")
    chat_file = manager.new_chat("demo")

    events = list(manager.chat_stream("demo", "hello", chat_file))

    assert [event["type"] for event in events] == ["start", "token", "token", "sources", "done"]
    assert events[3]["sources"] == [
        {"text": "source one", "score": 0.91},
        {"text": "source two", "score": 0.77},
    ]

    messages = manager.get_messages("demo", chat_file)
    assert messages[-1]["role"] == "assistant"
    assert messages[-1]["content"] == "stream answer"
    assert messages[-1]["additional_kwargs"] == {
        "sources": [
            {"text": "source one", "score": 0.91},
            {"text": "source two", "score": 0.77},
        ]
    }


def test_get_messages_keeps_legacy_sync_records_body_only_without_reconstructing_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(sm, "SESSION_ROOT", str(tmp_path / "sessions"))
    manager = SessionManager()
    manager.create("demo")
    chat_file = manager.new_chat("demo")
    chat_path = Path(manager.chats_dir("demo")) / chat_file

    store = SimpleChatStore()
    store.add_message("demo", ChatMessage(role=MessageRole.USER, content="hello"))
    store.add_message(
        "demo",
        ChatMessage(
            role=MessageRole.ASSISTANT,
            content="legacy answer\n\n---\n来源:\n[1] old inline source",
        ),
    )
    store.persist(str(chat_path))

    messages = manager.get_messages("demo", chat_file)

    assert messages == [
        {"role": "user", "content": "hello", "additional_kwargs": {}},
        {
            "role": "assistant",
            "content": "legacy answer\n\n---\n来源:\n[1] old inline source",
            "additional_kwargs": {},
        },
    ]

from pathlib import Path

from app.modules.session import session_manager as sm
from app.modules.session.session_manager import SessionManager


class _FakeCollection:
    def __init__(self, count: int = 1):
        self._count = count

    def count(self) -> int:
        return self._count


class _FakeClient:
    def __init__(self, collection: _FakeCollection):
        self._collection = collection

    def get_collection(self, _name: str) -> _FakeCollection:
        return self._collection


def _make_manager(tmp_path: Path, monkeypatch) -> SessionManager:
    monkeypatch.setattr(sm, "SESSION_ROOT", str(tmp_path / "sessions"))
    return SessionManager()


def test_chat_stream_persists_question_and_precheck_error_for_existing_new_chat(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.create("demo")
    chat_file = manager.new_chat("demo")

    events = list(manager.chat_stream("demo", "first question", chat_file))

    assert events[-1] == {"type": "error", "message": "会话 'demo' 未绑定知识库"}
    messages = manager.get_messages("demo", chat_file)
    assert [(m["role"], m["content"]) for m in messages] == [
        ("user", "first question"),
        ("assistant", "❌ 会话 'demo' 未绑定知识库"),
    ]


def test_chat_stream_persists_question_and_runtime_error_for_existing_new_chat(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    monkeypatch.setattr(sm._kb, "exists", lambda _name: True)
    monkeypatch.setattr(sm._kb, "vector_db_path", lambda _name: str(tmp_path / "vector-db"))
    monkeypatch.setattr(sm.chromadb, "PersistentClient", lambda path: _FakeClient(_FakeCollection(1)))

    def raise_connection_error():
        raise ConnectionError("model unavailable")

    monkeypatch.setattr(sm, "_ensure_models_initialized", raise_connection_error)

    manager.create("demo")
    manager.bind("demo", "kb1")
    chat_file = manager.new_chat("demo")

    events = list(manager.chat_stream("demo", "first question", chat_file))

    assert events[-1] == {"type": "error", "message": "model unavailable"}
    messages = manager.get_messages("demo", chat_file)
    assert [(m["role"], m["content"]) for m in messages] == [
        ("user", "first question"),
        ("assistant", "❌ model unavailable"),
    ]

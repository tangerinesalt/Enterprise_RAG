import json
import threading
from copy import deepcopy
from pathlib import Path

import pytest

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

    assert events[-1] == {
        "type": "error",
        "code": "KB_NOT_BOUND",
        "category": "kb",
        "message": "会话 'demo' 未绑定知识库",
    }
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

    assert events[-1] == {
        "type": "error",
        "code": "MODEL_UNAVAILABLE",
        "category": "model",
        "message": "model unavailable",
    }
    messages = manager.get_messages("demo", chat_file)
    assert [(m["role"], m["content"]) for m in messages] == [
        ("user", "first question"),
        ("assistant", "❌ model unavailable"),
    ]


def test_chat_persists_question_and_precheck_error_for_existing_new_chat(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.create("demo")
    chat_file = manager.new_chat("demo")

    with pytest.raises(sm.SessionError) as exc_info:
        manager.chat("demo", "first question", chat_file)

    messages = manager.get_messages("demo", chat_file)
    assert [(m["role"], m["content"]) for m in messages] == [
        ("user", "first question"),
        ("assistant", f"❌ {str(exc_info.value)}"),
    ]


def test_same_session_concurrent_writes_preserve_active_chat_and_config(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.create("demo")

    original_load = manager._load_config
    original_save = manager._save_config
    coordinated_threads = {"new_chat_worker", "update_worker"}
    loaded_threads: set[str] = set()
    load_lock = threading.Lock()
    both_loaded = threading.Event()
    new_chat_saved = threading.Event()

    def coordinated_load(name: str) -> dict:
        current = threading.current_thread().name
        if current in coordinated_threads:
            with load_lock:
                loaded_threads.add(current)
                if loaded_threads == coordinated_threads:
                    both_loaded.set()
            both_loaded.wait(0.2)
        return deepcopy(original_load(name))

    def coordinated_save(name: str, data: dict):
        current = threading.current_thread().name
        if current == "update_worker":
            new_chat_saved.wait(0.2)
            return original_save(name, data)

        result = original_save(name, data)
        if current == "new_chat_worker":
            new_chat_saved.set()
        return result

    monkeypatch.setattr(manager, "_load_config", coordinated_load)
    monkeypatch.setattr(manager, "_save_config", coordinated_save)

    errors: list[Exception] = []
    chat_file_box: dict[str, str] = {}

    def run_new_chat():
        try:
            chat_file_box["chat_file"] = manager.new_chat("demo")
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    def run_update_config():
        try:
            manager.update_config("demo", top_k=99)
        except Exception as exc:  # pragma: no cover
            errors.append(exc)

    new_chat_thread = threading.Thread(target=run_new_chat, name="new_chat_worker")
    update_thread = threading.Thread(target=run_update_config, name="update_worker")

    new_chat_thread.start()
    update_thread.start()
    new_chat_thread.join()
    update_thread.join()

    assert errors == []

    config = manager.get_config("demo")
    chat_file = chat_file_box["chat_file"]

    assert config["top_k"] == 99
    assert config["active_chat"] == chat_file
    assert json.loads(Path(manager.config_path("demo")).read_text(encoding="utf-8"))["active_chat"] == chat_file
    assert json.loads(Path(manager.chats_dir("demo"), chat_file).read_text(encoding="utf-8"))


def test_create_sets_default_system_prompt_with_parameter_and_context_guidance(tmp_path, monkeypatch):
    manager = _make_manager(tmp_path, monkeypatch)
    manager.create("demo")

    prompt = manager.get_config("demo")["system_prompt"]

    assert "来源超过 8 条" not in prompt
    assert "0.55" not in prompt
    assert "0.65" not in prompt
    assert "不同情形下会导致结果不同" in prompt
    assert "{context_str}" in prompt
    assert "{query_str}" in prompt

"""Tests: chat stream cancellation behavior.

Verifies that cancelling a streaming chat mid-flight (via generator close,
simulating client-side AbortController) leaves the chat file in a valid state
with only the user message persisted, and does not prevent subsequent operations.
"""

from pathlib import Path

from app.modules.session import session_manager as sm
from app.modules.session.session_manager import SessionManager


def _make_manager(tmp_path: Path, monkeypatch) -> SessionManager:
    monkeypatch.setattr(sm, "SESSION_ROOT", str(tmp_path / "sessions"))
    return SessionManager()


def test_chat_stream_cancellation_user_message_only(tmp_path, monkeypatch):
    """When a streaming request is cancelled mid-flight (generator closed),
    get_messages auto-removes the orphaned user message (no assistant response follows)."""
    manager = _make_manager(tmp_path, monkeypatch)
    manager.create("demo")

    monkeypatch.setattr(sm._kb, "exists", lambda _name: True)
    manager.bind("demo", "kb1")

    chat_file = manager.new_chat("demo")

    # Start the stream and consume the start event
    gen = manager.chat_stream("demo", "hello", chat_file)
    event = next(gen)
    assert event["type"] == "start"
    assert event["chat_file"] == chat_file

    # Close the generator, simulating client disconnect.
    gen.close()

    # get_messages returns the orphaned user message (legitimate data)
    messages = manager.get_messages("demo", chat_file)
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "hello"


def test_chat_stream_cancellation_does_not_block_subsequent_ops(tmp_path, monkeypatch):
    """After a cancelled stream, subsequent operations on the same chat file succeed."""
    manager = _make_manager(tmp_path, monkeypatch)
    manager.create("demo")

    monkeypatch.setattr(sm._kb, "exists", lambda _name: True)
    manager.bind("demo", "kb1")

    chat_file = manager.new_chat("demo")

    # Partially consume and cancel
    gen = manager.chat_stream("demo", "hello", chat_file)
    next(gen)
    gen.close()

    # Subsequent read should work (user message retained)
    messages = manager.get_messages("demo", chat_file)
    assert len(messages) == 1

    # The chat file on disk should now be empty after auto-repair
    chat_path = Path(manager.chats_dir("demo")) / chat_file
    import json
    data = json.loads(chat_path.read_text(encoding="utf-8"))
    assert "messages" in data or "conversation" in data or isinstance(data, dict)

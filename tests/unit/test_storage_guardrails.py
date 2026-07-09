from pathlib import Path

import pytest

from app.modules import session as session_pkg
from app.modules.kb_manager import KnowledgeBase, KnowledgeBaseError
from app.modules.session import SessionError, SessionManager


@pytest.mark.parametrize(
    "name",
    [
        "",
        "   ",
        ".",
        "..",
        "demo/sub",
        r"demo\sub",
        "demo.",
        "demo ",
        "CON",
        "con.txt",
        "LPT1",
        r"C:\demo",
        r"\\server\share",
        "bad<",
        "bad>",
        'bad"',
        "bad|",
        "bad?",
        "bad*",
        "bad:",
    ],
)
def test_kb_create_rejects_invalid_storage_names(tmp_path: Path, name: str):
    kb = KnowledgeBase(str(tmp_path / "kb-root"))

    with pytest.raises(KnowledgeBaseError):
        kb.create(name)


@pytest.mark.parametrize(
    "name",
    [
        "",
        "   ",
        ".",
        "..",
        "demo/sub",
        r"demo\sub",
        "demo.",
        "demo ",
        "AUX",
        "com1",
        r"C:\demo",
        r"\\server\share",
        "bad<",
        "bad>",
        'bad"',
        "bad|",
        "bad?",
        "bad*",
        "bad:",
    ],
)
def test_session_create_rejects_invalid_storage_names(tmp_path: Path, monkeypatch, name: str):
    monkeypatch.setattr(session_pkg.session_manager, "SESSION_ROOT", str(tmp_path / "sessions"))
    manager = SessionManager()

    with pytest.raises(SessionError):
        manager.create(name)


def test_kb_delete_file_rejects_traversal_target(tmp_path: Path):
    kb = KnowledgeBase(str(tmp_path / "kb-root"))
    kb.create("demo")
    valid_path = Path(kb.file_path("demo", "ok.txt"))
    valid_path.write_text("ok", encoding="utf-8")

    with pytest.raises(KnowledgeBaseError):
        kb.delete_file("demo", "../outside.txt")


def test_session_get_messages_rejects_traversal_chat_file(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(session_pkg.session_manager, "SESSION_ROOT", str(tmp_path / "sessions"))
    manager = SessionManager()
    manager.create("demo")
    manager.new_chat("demo")

    with pytest.raises(SessionError):
        manager.get_messages("demo", "../other.json")

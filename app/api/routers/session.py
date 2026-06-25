"""会话 REST API。"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.api.schemas import (
    SessionCreateRequest,
    SessionBindRequest,
    SessionNewChatRequest,
    SessionSelectChatRequest,
    SessionChatRequest,
)
from app.modules.session import SessionManager, SessionError

router = APIRouter()

_session = SessionManager()


def _ok(data=None):
    return {"ok": True, "data": data}

def _err(msg: str, status: int = 400):
    return JSONResponse(status_code=status, content={"ok": False, "error": msg})


@router.get("")
def list_sessions():
    """列出所有会话"""
    sessions = _session.list_all()
    return _ok(sessions)


@router.post("")
def create_session(body: SessionCreateRequest):
    """创建会话"""
    try:
        _session.create(body.name)
        return _ok({"name": body.name})
    except SessionError as e:
        return _err(str(e))


@router.get("/{name}")
def get_session(name: str):
    """会话详情"""
    try:
        info = _session.info(name)
        return _ok(info)
    except SessionError as e:
        return _err(str(e), 404)


@router.delete("/{name}")
def delete_session(name: str):
    """删除会话"""
    try:
        _session.delete(name)
        return _ok({"name": name})
    except SessionError as e:
        return _err(str(e), 404)


@router.post("/bind")
def bind_session(body: SessionBindRequest):
    """绑定知识库到会话"""
    try:
        _session.bind(body.name, body.kb_name)
        return _ok({"name": body.name, "kb_name": body.kb_name})
    except SessionError as e:
        return _err(str(e))


@router.post("/new")
def new_chat(body: SessionNewChatRequest):
    """在会话中新建一条聊天"""
    try:
        filename = _session.new_chat(body.name)
        return _ok({"name": body.name, "chat_file": filename})
    except SessionError as e:
        return _err(str(e))


@router.post("/select")
def select_chat(body: SessionSelectChatRequest):
    """切换到某条历史聊天"""
    try:
        _session.select_chat(body.name, body.chat_file)
        return _ok({"name": body.name, "chat_file": body.chat_file})
    except SessionError as e:
        return _err(str(e))


@router.post("/chat")
def chat(body: SessionChatRequest):
    """聊天：检索 → 生成 → 持久化"""
    try:
        result = _session.chat(body.name, body.query, body.chat_file)
        return _ok({
            "answer": result["answer"],
            "sources": result["sources"],
            "chat_file": result["chat_file"],
        })
    except SessionError as e:
        return _err(str(e))


@router.get("/{name}/chats")
def list_chats(name: str):
    """列出会话的聊天文件"""
    try:
        chats = _session.list_chats(name)
        return _ok({"name": name, "chats": chats})
    except SessionError as e:
        return _err(str(e), 404)

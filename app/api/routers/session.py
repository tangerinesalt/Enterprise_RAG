"""会话 REST API。"""

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.schemas import (
    SessionCreateRequest,
    SessionBindRequest,
    SessionNewChatRequest,
    SessionSelectChatRequest,
    SessionChatRequest,
)
from app.modules.session import SessionManager, SessionError
from app.utils.timing import timed

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
@timed("session_chat", warn=2.0, error=10.0)
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


@router.post("/chat/stream")
async def chat_stream(body: SessionChatRequest):
    """聊天流式接口（SSE）。逐 token 推送 LLM 生成结果。"""

    def generate():
        for event in _session.chat_stream(body.name, body.query, body.chat_file):
            etype = event["type"]
            if etype == "error":
                yield f"event: error\ndata: {json.dumps({'message': event['message']})}\n\n"
            elif etype == "start":
                yield f"event: start\ndata: {json.dumps({'chat_file': event['chat_file']})}\n\n"
            elif etype == "token":
                yield f"event: token\ndata: {json.dumps({'token': event['token']})}\n\n"
            elif etype == "sources":
                yield f"event: sources\ndata: {json.dumps({'sources': event['sources']})}\n\n"
            elif etype == "done":
                yield f"event: done\ndata: {json.dumps({'chat_file': event['chat_file']})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.delete("/{name}/chats/{chat_file}")
def delete_chat(name: str, chat_file: str):
    """删除会话中的单条聊天"""
    try:
        _session.delete(name, chat_file)
        return _ok({"name": name, "chat_file": chat_file})
    except SessionError as e:
        return _err(str(e), 404)


@router.get("/{name}/chats")
def list_chats(name: str):
    """列出会话的聊天文件"""
    try:
        chats = _session.list_chats(name)
        return _ok({"name": name, "chats": chats})
    except SessionError as e:
        return _err(str(e), 404)


@router.get("/{name}/chats/{chat_file}")
def get_chat_messages(name: str, chat_file: str):
    """获取指定聊天的消息记录"""
    try:
        messages = _session.get_messages(name, chat_file)
        return _ok({"name": name, "chat_file": chat_file, "messages": messages})
    except SessionError as e:
        return _err(str(e), 404)

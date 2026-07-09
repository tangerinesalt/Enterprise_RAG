"""会话 REST API。"""

import json

from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.schemas import (
    SessionBindRequest,
    SessionChatRequest,
    SessionConfigUpdateRequest,
    SessionCreateRequest,
    SessionNewChatRequest,
    SessionSelectChatRequest,
)
from app.modules.session import SessionError, SessionManager, SessionPathError

router = APIRouter()

_session = SessionManager()


def _ok(data=None):
    return {"ok": True, "data": data}


def _err(msg: str, status: int = 400):
    return JSONResponse(status_code=status, content={"ok": False, "error": msg})


def _session_error_status(exc: Exception, missing_status: int = 404) -> int:
    return 400 if isinstance(exc, SessionPathError) else missing_status


@router.get("")
def list_sessions():
    return _ok(_session.list_all())


@router.post("")
def create_session(body: SessionCreateRequest):
    try:
        _session.create(body.name)
        return _ok({"name": body.name})
    except SessionError as exc:
        return _err(str(exc), _session_error_status(exc, 400))


@router.get("/{name}")
def get_session(name: str):
    try:
        return _ok(_session.info(name))
    except SessionError as exc:
        return _err(str(exc), _session_error_status(exc))


@router.delete("/{name}")
def delete_session(name: str):
    try:
        _session.delete(name)
        return _ok({"name": name})
    except SessionError as exc:
        return _err(str(exc), _session_error_status(exc))


@router.post("/bind")
def bind_session(body: SessionBindRequest):
    try:
        _session.bind(body.name, body.kb_name)
        return _ok({"name": body.name, "kb_name": body.kb_name})
    except SessionError as exc:
        return _err(str(exc), _session_error_status(exc, 400))


@router.post("/new")
def new_chat(body: SessionNewChatRequest):
    try:
        filename = _session.new_chat(body.name)
        return _ok({"name": body.name, "chat_file": filename})
    except SessionError as exc:
        return _err(str(exc), _session_error_status(exc, 400))


@router.post("/select")
def select_chat(body: SessionSelectChatRequest):
    try:
        _session.select_chat(body.name, body.chat_file)
        return _ok({"name": body.name, "chat_file": body.chat_file})
    except SessionError as exc:
        return _err(str(exc), _session_error_status(exc, 400))


@router.post("/chat")
def chat(body: SessionChatRequest):
    try:
        result = _session.chat(body.name, body.query, body.chat_file)
        return _ok({"answer": result["answer"], "sources": result["sources"], "chat_file": result["chat_file"]})
    except SessionError as exc:
        return _err(str(exc), _session_error_status(exc, 400))


@router.post("/chat/stream")
def chat_stream(body: SessionChatRequest):
    def generate():
        for event in _session.chat_stream(body.name, body.query, body.chat_file):
            event_type = event["type"]
            if event_type == "error":
                payload = {"code": event["code"], "category": event["category"], "message": event["message"]}
                yield f"event: error\ndata: {json.dumps(payload)}\n\n"
            elif event_type == "start":
                yield f"event: start\ndata: {json.dumps({'chat_file': event['chat_file']})}\n\n"
            elif event_type == "token":
                yield f"event: token\ndata: {json.dumps({'token': event['token']})}\n\n"
            elif event_type == "sources":
                yield f"event: sources\ndata: {json.dumps({'sources': event['sources']})}\n\n"
            elif event_type == "done":
                yield f"event: done\ndata: {json.dumps({'chat_file': event['chat_file']})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.delete("/{name}/chats/{chat_file}")
def delete_chat(name: str, chat_file: str):
    try:
        _session.delete(name, chat_file)
        return _ok({"name": name, "chat_file": chat_file})
    except SessionError as exc:
        return _err(str(exc), _session_error_status(exc))


@router.patch("/{name}/config")
def update_session_config(name: str, body: SessionConfigUpdateRequest):
    try:
        kwargs = {}
        if body.top_k is not None:
            kwargs["top_k"] = body.top_k
        if body.top_n is not None:
            kwargs["top_n"] = body.top_n
        if body.system_prompt is not None:
            kwargs["system_prompt"] = body.system_prompt
        if not kwargs:
            return _err("未提供需要更新的参数")
        return _ok(_session.update_config(name, **kwargs))
    except SessionError as exc:
        return _err(str(exc), _session_error_status(exc, 400))


@router.get("/{name}/chats")
def list_chats(name: str):
    try:
        return _ok({"name": name, "chats": _session.list_chats(name)})
    except SessionError as exc:
        return _err(str(exc), _session_error_status(exc))


@router.get("/{name}/chats/{chat_file}")
def get_chat_messages(name: str, chat_file: str):
    try:
        messages = _session.get_messages(name, chat_file)
        return _ok({"name": name, "chat_file": chat_file, "messages": messages})
    except SessionError as exc:
        return _err(str(exc), _session_error_status(exc))

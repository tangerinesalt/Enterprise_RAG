"""Pydantic 请求/响应模型。"""

from pydantic import BaseModel
from typing import Optional


# ── 通用响应 ───────────────────────────────

class ApiResponse(BaseModel):
    ok: bool
    data: Optional[object] = None
    error: Optional[str] = None


# ── 知识库 ─────────────────────────────────

class KbCreateRequest(BaseModel):
    name: str

class KbIndexRequest(BaseModel):
    name: str
    target: Optional[str] = None
    all: bool = False

class KbReindexRequest(BaseModel):
    name: str
    filename: str


# ── 会话 ───────────────────────────────────

class SessionCreateRequest(BaseModel):
    name: str

class SessionBindRequest(BaseModel):
    name: str
    kb_name: str

class SessionNewChatRequest(BaseModel):
    name: str

class SessionSelectChatRequest(BaseModel):
    name: str
    chat_file: str

class SessionChatRequest(BaseModel):
    name: str
    query: str
    chat_file: Optional[str] = None

class SessionConfigUpdateRequest(BaseModel):
    top_k: Optional[int] = None
    top_n: Optional[int] = None

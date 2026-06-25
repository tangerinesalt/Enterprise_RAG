"""FastAPI 应用入口。

启动：
    uvicorn app.api.server:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import kb, session

app = FastAPI(
    title="RAG V",
    description="企业级 RAG 应用 REST API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kb.router, prefix="/api/kb", tags=["知识库"])
app.include_router(session.router, prefix="/api/session", tags=["会话"])


@app.get("/api/health", tags=["系统"])
def health_check():
    return {"ok": True, "status": "running"}

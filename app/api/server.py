"""FastAPI 应用入口。

启动：
    uvicorn app.api.server:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import kb, session
from app.utils.logging import get_logger


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """服务器启动时预热 LLM + Embedding 模型，消除首次请求延迟。"""
    try:
        from config.init import init_models
        init_models()
    except Exception as e:
        logger.error("model_init lifespan failed: %s", e)
    yield


app = FastAPI(
    title="RAG V",
    description="企业级 RAG 应用 REST API",
    version="0.1.0",
    lifespan=lifespan,
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

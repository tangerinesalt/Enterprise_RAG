"""FastAPI 应用入口。

启动：
    uvicorn app.api.server:app --reload --port 8000
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers import kb, session
from app.utils.timing import get_stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    """服务器启动时预热 LLM + Embedding 模型，消除首次请求延迟。"""
    t0 = time.time()
    try:
        from config.init import init_models
        init_models()
        elapsed = time.time() - t0
        level = "WARN" if elapsed > 1 else "OK"
        color = "\033[93m" if elapsed > 1 else "\033[92m"
        print(f"{color}[TIMING][{level}] model_init lifespan: {elapsed:.3f}s\033[0m", flush=True)
    except Exception as e:
        print(f"\033[91m[TIMING][ERROR] model_init lifespan failed: {e}\033[0m", flush=True)
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


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """记录每个 HTTP 请求的总耗时"""
    t0 = time.time()
    response = await call_next(request)
    elapsed = time.time() - t0
    level = "WARN" if elapsed > 1 else "OK"
    color = "\033[93m" if elapsed > 1 else "\033[92m"
    print(f"{color}[TIMING][{level}] {request.method} {request.url.path} → {elapsed:.3f}s\033[0m")
    return response


@app.get("/api/health", tags=["系统"])
def health_check():
    return {"ok": True, "status": "running"}


@app.get("/api/performance", tags=["系统"])
def performance_stats():
    """获取最近请求的耗时统计"""
    stats = get_stats()
    return {"ok": True, "data": stats}

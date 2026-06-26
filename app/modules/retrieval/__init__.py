"""检索模块 — 向量检索、BM25 混合检索、RRF 融合。"""

from .retriever import build_retriever

__all__ = ["build_retriever"]

"""
Hybrid retriever: vector search + BM25 with optional RRF fusion.
"""

import os

import jieba
from llama_index.core import QueryBundle
from llama_index.core.retrievers import BaseRetriever, VectorIndexRetriever
from llama_index.core.schema import TextNode
from llama_index.retrievers.bm25 import BM25Retriever

from app.modules.kb_manager import KnowledgeBase


def _chinese_tokenizer(text: str) -> list[str]:
    return list(jieba.cut(text))


_bm25_index_cache: dict[tuple[str, int], tuple[int, BM25Retriever | None]] = {}
_kb = KnowledgeBase()


def _build_bm25_retriever(kb_name: str, top_k: int = 5, collection=None) -> BM25Retriever | None:
    current_version = _kb.get_corpus_version(kb_name)
    cache_key = (kb_name, top_k)
    cached = _bm25_index_cache.get(cache_key)
    if cached and cached[0] == current_version:
        return cached[1]

    if collection is None:
        import chromadb

        db_path = _kb.vector_db_path(kb_name)
        if not os.path.isdir(db_path):
            _bm25_index_cache[cache_key] = (current_version, None)
            return None
        try:
            collection = chromadb.PersistentClient(path=db_path).get_collection("kb_index")
        except Exception:
            _bm25_index_cache[cache_key] = (current_version, None)
            return None

    try:
        data = collection.get(include=["documents"])
    except Exception:
        _bm25_index_cache[cache_key] = (current_version, None)
        return None

    if not data or not data["ids"]:
        _bm25_index_cache[cache_key] = (current_version, None)
        return None

    nodes = []
    for doc_id, text in zip(data["ids"], data["documents"]):
        node = TextNode(text=text)
        node.node_id = doc_id
        nodes.append(node)

    retriever = BM25Retriever.from_defaults(
        nodes=nodes,
        tokenizer=_chinese_tokenizer,
        similarity_top_k=top_k,
    )
    _bm25_index_cache[cache_key] = (current_version, retriever)
    return retriever


def _rrf_fusion(
    vector_nodes: list,
    bm25_nodes: list,
    k: int = 60,
    top_k: int = 5,
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
) -> list:
    rank_scores: dict[str, float] = {}

    for rank, node in enumerate(vector_nodes):
        node_id = node.node_id if hasattr(node, "node_id") else id(node)
        rank_scores[node_id] = rank_scores.get(node_id, 0) + vector_weight / (k + rank + 1)

    for rank, node in enumerate(bm25_nodes):
        node_id = node.node_id if hasattr(node, "node_id") else id(node)
        rank_scores[node_id] = rank_scores.get(node_id, 0) + bm25_weight / (k + rank + 1)

    scored = []
    seen = set()
    for node in vector_nodes + bm25_nodes:
        node_id = node.node_id if hasattr(node, "node_id") else id(node)
        if node_id in seen:
            continue
        seen.add(node_id)
        node.score = rank_scores.get(node_id, 0)
        scored.append(node)

    scored.sort(key=lambda node: node.score or 0, reverse=True)
    return scored[:top_k]


class _ScoreThresholdRetriever(BaseRetriever):
    def __init__(self, retriever, threshold=0.2):
        self._retriever = retriever
        self._threshold = threshold

    def _retrieve(self, query_bundle: QueryBundle):
        nodes = self._retriever.retrieve(query_bundle)
        return [node for node in nodes if node.score and node.score >= self._threshold]


class _HybridRetriever(BaseRetriever):
    def __init__(self, vector_retriever, bm25_retriever, top_k: int = 5, vector_weight=0.7, bm25_weight=0.3):
        self._vector = vector_retriever
        self._bm25 = bm25_retriever
        self._top_k = top_k
        self._vector_weight = vector_weight
        self._bm25_weight = bm25_weight

    def _retrieve(self, query_bundle: QueryBundle):
        query_str = query_bundle.query_str if hasattr(query_bundle, "query_str") else str(query_bundle)
        vector_nodes = self._vector.retrieve(query_bundle)
        bm25_nodes = self._bm25.retrieve(query_str)
        return _rrf_fusion(
            vector_nodes,
            bm25_nodes,
            top_k=self._top_k,
            vector_weight=self._vector_weight,
            bm25_weight=self._bm25_weight,
        )


def build_retriever(index, kb_name=None, top_k=5, mode="hybrid"):
    threshold_retriever = _ScoreThresholdRetriever(
        VectorIndexRetriever(
            index=index,
            similarity_top_k=top_k,
        ),
        threshold=0.2,
    )

    if kb_name and mode == "hybrid":
        collection = getattr(index.vector_store, "_collection", None)
        bm25_retriever = _build_bm25_retriever(kb_name, top_k=top_k, collection=collection)
        if bm25_retriever is not None:
            return _HybridRetriever(threshold_retriever, bm25_retriever, top_k=top_k)

    return threshold_retriever

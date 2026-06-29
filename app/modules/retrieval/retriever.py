"""
Hybrid Retriever — 向量检索 + BM25 混合检索，支持 MetadataFilters 和 RRF 融合。

用法：
    from app.modules.retrieval import build_retriever
    retriever = build_retriever(index, kb_name="my_kb")
    nodes = retriever.retrieve(query_bundle)
"""

import os

from llama_index.core import QueryBundle
from llama_index.core.retrievers import VectorIndexRetriever, BaseRetriever
from llama_index.core.schema import TextNode
from llama_index.retrievers.bm25 import BM25Retriever
import jieba


# ── 中文分词器（用于 BM25）─────────────────
def _chinese_tokenizer(text: str) -> list[str]:
    return list(jieba.cut(text))


# ── BM25 索引缓存（按 kb_name）─────────────
_bm25_index_cache: dict[str, BM25Retriever] = {}


def _load_kb_paragraphs(kb_name: str) -> list[str]:
    """从知识库源文件读取原始段落（按 \\n\\n 分割），供 BM25 构建独立索引。"""
    from app.modules.kb_manager import KnowledgeBase
    _kb = KnowledgeBase()
    fdir = _kb.files_path(kb_name)
    if not os.path.isdir(fdir):
        return []

    paragraphs = []
    for root, _, files in os.walk(fdir):
        for fname in sorted(files):
            if not fname.endswith(".txt"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8-sig") as f:
                    text = f.read()
            except Exception:
                continue
            # 按 \n\n 分割段落（兼容 .txt 和 .md）
            for para in text.split("\n\n"):
                para = para.strip()
                if para:
                    paragraphs.append(para)
    return paragraphs


def _build_bm25_retriever(kb_name: str, top_k: int = 5) -> BM25Retriever:
    """构建（或从缓存取）中文 BM25 检索器。

    基于知识库源文件的原始段落（\\n\\n 分割），而非向量索引的合并 chunk。
    """
    if kb_name in _bm25_index_cache:
        return _bm25_index_cache[kb_name]

    paragraphs = _load_kb_paragraphs(kb_name)
    if not paragraphs:
        # fallback：返回空检索器
        retriever = BM25Retriever.from_defaults(
            nodes=[], tokenizer=_chinese_tokenizer, similarity_top_k=top_k
        )
        _bm25_index_cache[kb_name] = retriever
        return retriever

    # BM25 需要 TextNode 对象（纯字符串会报错）
    para_nodes = [TextNode(text=p) for p in paragraphs]
    retriever = BM25Retriever.from_defaults(
        nodes=para_nodes,
        tokenizer=_chinese_tokenizer,
        similarity_top_k=top_k,
    )
    _bm25_index_cache[kb_name] = retriever
    return retriever


# ── RRF 融合 ──────────────────────────────
def _rrf_fusion(
    vector_nodes: list,
    bm25_nodes: list,
    k: int = 60,
    top_k: int = 5,
    vector_weight: float = 0.7,
    bm25_weight: float = 0.3,
) -> list:
    """加权 Reciprocal Rank Fusion 融合向量 + BM25 的检索结果。

    vector_weight / bm25_weight 控制两路贡献比例，默认 0.7/0.3。
    基于测试：bge-m3 对正常查询全部排 #1，BM25 波动大，向量权重应更高。
    """
    rank_scores: dict[str, float] = {}

    for rank, node in enumerate(vector_nodes):
        node_id = node.node_id if hasattr(node, 'node_id') else id(node)
        rank_scores[node_id] = rank_scores.get(node_id, 0) + vector_weight / (k + rank + 1)

    for rank, node in enumerate(bm25_nodes):
        node_id = node.node_id if hasattr(node, 'node_id') else id(node)
        rank_scores[node_id] = rank_scores.get(node_id, 0) + bm25_weight / (k + rank + 1)

    # 去重 + 排序
    scored = []
    seen = set()
    for node in vector_nodes + bm25_nodes:
        nid = node.node_id if hasattr(node, 'node_id') else id(node)
        if nid in seen:
            continue
        seen.add(nid)
        node.score = rank_scores.get(nid, 0)
        scored.append(node)

    scored.sort(key=lambda n: n.score or 0, reverse=True)
    return scored[:top_k]


# ── 分数阈值包装 ──────────────────────────
class _ScoreThresholdRetriever(BaseRetriever):
    """包装 VectorIndexRetriever，按最低分数阈值过滤节点。"""

    def __init__(self, retriever, threshold=0.2):
        self._retriever = retriever
        self._threshold = threshold

    def _retrieve(self, query_bundle: QueryBundle):
        nodes = self._retriever.retrieve(query_bundle)
        return [n for n in nodes if n.score and n.score >= self._threshold]


# ── 混合检索器 ────────────────────────────
class _HybridRetriever(BaseRetriever):
    """向量 + BM25 混合检索器，使用加权 RRF 融合排序。"""

    def __init__(self, vector_retriever, bm25_retriever, top_k: int = 5,
                 vector_weight=0.7, bm25_weight=0.3):
        self._vector = vector_retriever
        self._bm25 = bm25_retriever
        self._top_k = top_k
        self._vector_weight = vector_weight
        self._bm25_weight = bm25_weight

    def _retrieve(self, query_bundle: QueryBundle):
        query_str = query_bundle.query_str if hasattr(query_bundle, 'query_str') else str(query_bundle)
        vec_nodes = self._vector.retrieve(query_bundle)
        bm25_nodes = self._bm25.retrieve(query_str)
        return _rrf_fusion(
            vec_nodes, bm25_nodes, top_k=self._top_k,
            vector_weight=self._vector_weight, bm25_weight=self._bm25_weight,
        )


# ── 公开入口 ──────────────────────────────
def build_retriever(index, kb_name=None, top_k=5, mode="hybrid"):
    """
    构建检索器。

    参数：
        index: VectorStoreIndex 实例
        kb_name: 知识库名称（传此值启用 BM25 混合检索）
        top_k: 向量/BM25 召回数及 RRF 保留数（默认 5）
        mode: "hybrid"（默认，向量+BM25+RRF）或 "vector-only"（仅向量）

    返回：
        BaseRetriever 实例
    """
    threshold_retriever = _ScoreThresholdRetriever(
        VectorIndexRetriever(
            index=index,
            similarity_top_k=top_k,
        ),
        threshold=0.2,
    )

    if kb_name and mode == "hybrid":
        bm25_retriever = _build_bm25_retriever(kb_name, top_k=top_k)
        return _HybridRetriever(threshold_retriever, bm25_retriever, top_k=top_k)

    # mode == "vector-only" 或未传 kb_name 时走纯向量路径
    return threshold_retriever

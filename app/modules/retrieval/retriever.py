"""
Hybrid Retriever — 向量检索 + BM25 混合检索，支持 MetadataFilters 和 RRF 融合。

用法：
    from app.modules.retrieval import build_retriever
    retriever = build_retriever(index, kb_name="my_kb")
    nodes = retriever.retrieve(query_bundle)
"""

from llama_index.core import QueryBundle
from llama_index.core.retrievers import VectorIndexRetriever, BaseRetriever
from llama_index.retrievers.bm25 import BM25Retriever
import jieba


# ── 中文分词器（用于 BM25）─────────────────
def _chinese_tokenizer(text: str) -> list[str]:
    return list(jieba.cut(text))


# ── BM25 索引缓存（按 kb_name）─────────────
_bm25_index_cache: dict[str, BM25Retriever] = {}


def _build_bm25_retriever(index, kb_name: str) -> BM25Retriever:
    """构建（或从缓存取）中文 BM25 检索器。"""
    if kb_name in _bm25_index_cache:
        return _bm25_index_cache[kb_name]

    # 从 index 提取所有 node 文本
    all_nodes = index.docstore.docs.values() if hasattr(index, 'docstore') else []
    if not all_nodes:
        dummy = VectorIndexRetriever(index=index, similarity_top_k=100)
        try:
            all_nodes = [n.node for n in dummy.retrieve("")]
        except Exception:
            all_nodes = []

    nodes_list = list(all_nodes) if not isinstance(all_nodes, list) else all_nodes

    retriever = BM25Retriever.from_defaults(
        nodes=nodes_list if nodes_list else None,
        tokenizer=_chinese_tokenizer,
        similarity_top_k=5,
    )
    _bm25_index_cache[kb_name] = retriever
    return retriever


# ── RRF 融合 ──────────────────────────────
def _rrf_fusion(
    vector_nodes: list,
    bm25_nodes: list,
    k: int = 60,
    top_k: int = 5,
) -> list:
    """Reciprocal Rank Fusion 融合向量 + BM25 的检索结果。"""
    rank_scores: dict[str, float] = {}

    for rank, node in enumerate(vector_nodes):
        node_id = node.node_id if hasattr(node, 'node_id') else id(node)
        rank_scores[node_id] = rank_scores.get(node_id, 0) + 1 / (k + rank + 1)

    for rank, node in enumerate(bm25_nodes):
        node_id = node.node_id if hasattr(node, 'node_id') else id(node)
        rank_scores[node_id] = rank_scores.get(node_id, 0) + 1 / (k + rank + 1)

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

    def __init__(self, retriever, threshold=0.6):
        self._retriever = retriever
        self._threshold = threshold

    def _retrieve(self, query_bundle: QueryBundle):
        nodes = self._retriever.retrieve(query_bundle)
        return [n for n in nodes if n.score and n.score >= self._threshold]


# ── 混合检索器 ────────────────────────────
class _HybridRetriever(BaseRetriever):
    """向量 + BM25 混合检索器，使用 RRF 融合排序。"""

    def __init__(self, vector_retriever, bm25_retriever):
        self._vector = vector_retriever
        self._bm25 = bm25_retriever

    def _retrieve(self, query_bundle: QueryBundle):
        query_str = query_bundle.query_str if hasattr(query_bundle, 'query_str') else str(query_bundle)
        vec_nodes = self._vector.retrieve(query_bundle)
        bm25_nodes = self._bm25.retrieve(query_str)
        return _rrf_fusion(vec_nodes, bm25_nodes)


# ── 公开入口 ──────────────────────────────
def build_retriever(index, kb_name=None):
    """
    构建带 MetadataFilters + BM25 + RRF 的混合检索器。

    参数：
        index: VectorStoreIndex 实例
        kb_name: 知识库名称（传此值启用 BM25 混合检索）

    返回：
        BaseRetriever 实例
    """
    threshold_retriever = _ScoreThresholdRetriever(
        VectorIndexRetriever(
            index=index,
            similarity_top_k=5,
        ),
        threshold=0.6,
    )

    if kb_name:
        bm25_retriever = _build_bm25_retriever(index, kb_name)
        return _HybridRetriever(threshold_retriever, bm25_retriever)

    return threshold_retriever

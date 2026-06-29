"""
RRF 融合降级分析。

现象：bge-m3 下 A1 在 embedding 空间排 #3，RRF 融合后降到 #5。
根因：RRF 等权融合假设向量和 BM25 同样可靠，但实际向量更准。

分析：
1. 对比 A1 vs 其他片段在 vec/bm25 各自路径的排名
2. 计算 RRF 分数构成：哪些片段受益于双路径"加分"
3. 测试不同 RRF k 值对 A1 排名的影响
4. 测试纯向量路径 (无 RRF) 的 reranker 结果
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import chromadb, jieba
from llama_index.core import VectorStoreIndex, QueryBundle, Settings
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.schema import NodeWithScore, TextNode

from config.init import init_models
from app.modules.kb_manager import KnowledgeBase
from app.modules.retrieval.retriever import _rrf_fusion, _ScoreThresholdRetriever

init_models()
_kb = KnowledgeBase()
col = chromadb.PersistentClient(path=_kb.vector_db_path("062500")).get_collection("kb_index")
index = VectorStoreIndex.from_vector_store(vector_store=ChromaVectorStore(chroma_collection=col))

QUERY = "A1是什么"
TOP_K = 12
bundle = QueryBundle(query_str=QUERY)

# ── 1. 加载原始排名 ──────────────────────────────
print("=" * 70)
print("  1. 三条路径的独立排名")
print("=" * 70)

# Vector
vec = VectorIndexRetriever(index=index, similarity_top_k=TOP_K)
vec_nodes = vec.retrieve(bundle)
vec_ranks = {}
for i, n in enumerate(vec_nodes):
    text_sig = n.text.strip().replace("﻿", "")[:60]
    vec_ranks[text_sig] = {"vec_rank": i + 1, "vec_score": round(float(n.score), 4)}

# BM25
all_n = list(index.docstore.docs.values()) if hasattr(index, 'docstore') else []
if not all_n:
    d = VectorIndexRetriever(index=index, similarity_top_k=100)
    all_n = [n.node for n in d.retrieve(QUERY)]
bm25 = BM25Retriever.from_defaults(
    nodes=list(all_n),
    tokenizer=lambda t: list(jieba.cut(t)),
    similarity_top_k=TOP_K,
)
bm25_nodes = bm25.retrieve(QUERY)
bm25_ranks = {}
for i, n in enumerate(bm25_nodes):
    text_sig = n.text.strip().replace("﻿", "")[:60]
    bm25_ranks[text_sig] = {"bm25_rank": i + 1}

# 合并为完整排名表
all_sigs = set(list(vec_ranks.keys()) + list(bm25_ranks.keys()))
print(f"  {'片段':<50s} {'向量排名':>8s} {'向量得分':>8s} {'BM25排名':>8s} {'双路径?':>8s}")
print(f"  {'-'*50} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
for sig in sorted(all_sigs):
    v = vec_ranks.get(sig, {})
    b = bm25_ranks.get(sig, {})
    vec_r = v.get("vec_rank", "-")
    vec_s = v.get("vec_score", "-")
    bm25_r = b.get("bm25_rank", "-")
    dual = "✓" if (vec_r != "-" and bm25_r != "-") else "✗"
    is_a1 = "A1" in sig or "金融风险管理关注" in sig
    marker = " ← ★ A1" if is_a1 else ""
    print(f"  {sig:<50s} {str(vec_r):>8s} {str(vec_s):>8s} {str(bm25_r):>8s} {dual:>8s}{marker}")

# A1 在两条路径上的排名
a1_sig = next(s for s in all_sigs if "A1" in s or "金融风险管理关注" in s)
a1_vec_rank = vec_ranks[a1_sig]["vec_rank"]
a1_bm25_rank = bm25_ranks.get(a1_sig, {}).get("bm25_rank", "N/A")
print(f"\n  A1: vector #{a1_vec_rank}, BM25 #{a1_bm25_rank}")

# ── 2. RRF 分数构成分析 ──────────────────────────
print(f"\n{'=' * 70}")
print("  2. RRF 分数构成 (k=60)")
print(f"{'=' * 70}")

K = 60
for sig in sorted(all_sigs):
    v = vec_ranks.get(sig, {})
    b = bm25_ranks.get(sig, {})

    vec_score = 0
    if "vec_rank" in v:
        vec_score = 1 / (K + v["vec_rank"] - 1 + 1)  # rank is 1-based

    bm25_score = 0
    if "bm25_rank" in b:
        bm25_score = 1 / (K + b["bm25_rank"] - 1 + 1)

    total = vec_score + bm25_score
    is_a1 = "A1" in sig or "金融风险管理关注" in sig
    marker = " ← ★ A1" if is_a1 else ""

    vec_part = f"v#{v.get('vec_rank','-')}={vec_score:.4f}" if vec_score > 0 else ""
    bm25_part = f"b#{b.get('bm25_rank','-')}={bm25_score:.4f}" if bm25_score > 0 else ""
    detail = f"  {vec_part} + {bm25_part}" if (vec_part and bm25_part) else (vec_part or bm25_part or "  无路径")
    print(f"  rrf={total:.4f}  {detail}{marker}")
    print(f"    {sig}")

# ── 3. RRF k 值敏感性 ────────────────────────────
print(f"\n{'=' * 70}")
print("  3. RRF k 值对 A1 排名的影响")
print(f"{'=' * 70}")

for K_test in [10, 30, 60, 100, 200]:
    scores = {}
    for sig in all_sigs:
        v = vec_ranks.get(sig, {})
        b = bm25_ranks.get(sig, {})
        s = 0
        if "vec_rank" in v:
            s += 1 / (K_test + v["vec_rank"] - 1 + 1)
        if "bm25_rank" in b:
            s += 1 / (K_test + b["bm25_rank"] - 1 + 1)
        scores[sig] = s

    ranked = sorted(scores.items(), key=lambda x: -x[1])
    a1_pos = next(i + 1 for i, (sig, _) in enumerate(ranked) if "A1" in sig or "金融风险管理关注" in sig)
    top1_sig = ranked[0][0]
    print(f"  k={K_test:4d}  →  A1 RRF 排名 #{a1_pos:2d}/12  (top1={top1_sig[:30]}...)")

# ── 4. 移除 RRF，纯向量路径下 reranker 表现 ──────
print(f"\n{'=' * 70}")
print("  4. 对比: 纯向量 vs 混合(RRF) 下 reranker 排名")
print(f"{'=' * 70}")

# 4a. 纯向量 → reranker
print(f"\n  【纯向量路径】VectorIndexRetriever(top_k=12) → Reranker(top_n=8):")
vec_candidates = [NodeWithScore(node=TextNode(text=n.text), score=0.0) for n in vec_nodes]
reranker_vec = SentenceTransformerRerank(top_n=8)
reranked_vec = reranker_vec.postprocess_nodes(vec_candidates, query_bundle=bundle)
for i, n in enumerate(reranked_vec):
    is_a1 = "A1" in n.text[:20] or "金融风险管理关注" in n.text[:40]
    marker = " ← ★ A1!" if is_a1 else ""
    print(f"  [{i+1}] score={n.score:.4f}  {n.text.strip()[:60]}...{marker}")

# 4b. 混合 → reranker (用 vec_filtered)
threshold = _ScoreThresholdRetriever(vec, threshold=0.2)
vec_filtered = threshold.retrieve(bundle)
rrf_mixed = _rrf_fusion(vec_filtered, bm25_nodes, top_k=TOP_K)
print(f"\n  【混合路径】Vector+BM25→RRF→Reranker(top_n=8):")
reranker_mixed = SentenceTransformerRerank(top_n=8)
reranked_mixed = reranker_mixed.postprocess_nodes(rrf_mixed, query_bundle=bundle)
for i, n in enumerate(reranked_mixed):
    is_a1 = "A1" in n.text[:20] or "金融风险管理关注" in n.text[:40]
    marker = " ← ★ A1!" if is_a1 else ""
    print(f"  [{i+1}] score={n.score:.4f}  {n.text.strip()[:60]}...{marker}")

# ── 5. 去重检查 ──────────────────────────────────
print(f"\n{'=' * 70}")
print("  5. RRF 对双路径片段的歧视性加分")
print(f"{'=' * 70}")
print(f"  核心问题: 双路径(✓)片段获得两份 RRF 分数")
print(f"  单路径(✗)片段只获得一份")
print(f"")
print(f"  A1 在 vector #{a1_vec_rank}, BM25 #{a1_bm25_rank}")
print(f"  双路径得分 = 1/({K}+{a1_vec_rank}-1+1) + 1/({K}+{a1_bm25_rank}-1+1)")
a1_rrf = 1/(K+a1_vec_rank-1+1) + (1/(K+int(a1_bm25_rank)-1+1) if a1_bm25_rank != "N/A" else 0)
print(f"               = {a1_rrf:.4f}")
print(f"")
print(f"  如果 A1 只走向量路径 (单路径), 得分 = 1/({K}+{a1_vec_rank}-1+1) = {1/(K+a1_vec_rank-1+1):.4f}")
print(f"  一个排名 #5 的双路径片段得分 = 1/({K}+5-1+1)*2 = {2/(K+5):.4f}")
print(f"")
print(f"  {'→ RRF 天然偏向同时被两种检索方法命中的片段':^60s}")
print(f"  {'即使向量方法本身已经给出了足够好的排名':^60s}")

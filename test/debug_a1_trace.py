"""
A1 全链路追踪：从 embedding 到 reranker 的完整评分链分析。

对比两个关键问题：
1. "A1是什么" 在 embedding 空间中的真实排名
2. Reranker 如何重排序（对比 embedding cosine_sim vs reranker score）
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
KB_NAME = "062500"
QUERY = "A1是什么"

# ── 1. 加载 ChromaDB ──────────────────────────────
db = chromadb.PersistentClient(path=_kb.vector_db_path(KB_NAME))
col = db.get_collection("kb_index")
index = VectorStoreIndex.from_vector_store(vector_store=ChromaVectorStore(chroma_collection=col))
vector_count = col.count()
print(f"ChromaDB 向量总数: {vector_count}")
print("=" * 70)

# ── 2. Step 1: ChromaDB Embedding 原始排名 ──────
print(f"\n【Step 1】Embedding 空间: cosine_similarity 排名 (查询=\"{QUERY}\")")
print("-" * 70)

query_emb = Settings.embed_model.get_text_embedding(QUERY)
results = col.query(
    query_embeddings=[query_emb],
    n_results=vector_count,
    include=["documents", "distances", "metadatas", "embeddings"]
)

embedding_rank = []  # (orig_rank, text, cosine_sim)
for i, (doc, dist, meta, emb) in enumerate(zip(
    results["documents"][0], results["distances"][0],
    results["metadatas"][0], results["embeddings"][0]
)):
    cosine_sim = round(1 - dist, 4)
    is_a1 = "A1" in doc[:20] or "金融风险管理关注" in doc[:40]
    marker = " ← ★ A1 (正确答案)" if is_a1 else ""
    clip = doc.replace(chr(65279), "").replace("\n", " ")[:70]
    print(f"  #{i+1:2d}  cosine_sim={cosine_sim:.4f}  {clip}{marker}")
    embedding_rank.append({
        "rank": i + 1, "cosine_sim": cosine_sim,
        "text": doc, "is_a1": is_a1, "embedding": emb,
    })

# A1 在 embedding 空间的定位
a1_embed = [r for r in embedding_rank if r["is_a1"]][0]
print(f"\n  ★ A1 embedding 排名: #{a1_embed['rank']}/{vector_count}")
print(f"  ★ A1 cosine_similarity: {a1_embed['cosine_sim']:.4f}")

# ── 3. Step 2: VectorIndexRetriever + 阈值过滤 ───
print(f"\n【Step 2】VectorIndexRetriever + threshold=0.2 过滤")
print("-" * 70)
TOP_K = 12  # 放大到 12 确保覆盖所有候选

vec_retriever = VectorIndexRetriever(index=index, similarity_top_k=TOP_K)
threshold = _ScoreThresholdRetriever(vec_retriever, threshold=0.2)
bundle = QueryBundle(query_str=QUERY)
vec_filtered = threshold.retrieve(bundle)

print(f"  VectorIndexRetriever(相似度搜索 top_k={TOP_K}) → {len(vec_filtered)} 个通过 0.2 阈值")
for i, n in enumerate(vec_filtered):
    is_a1 = "A1" in n.text[:20] or "金融风险管理关注" in n.text[:40]
    marker = " ← ★ A1!" if is_a1 else ""
    print(f"  [{i+1}] score={n.score:.4f}{marker}  {n.text.strip()[:60]}...")

# ── 4. Step 3: BM25 检索 ──────────────────────────
print(f"\n【Step 3】BM25 检索 (jieba 分词, top_k={TOP_K})")
print("-" * 70)

# 从 index 拉 nodes
all_nodes = list(index.docstore.docs.values()) if hasattr(index, 'docstore') else []
if not all_nodes:
    dummy = VectorIndexRetriever(index=index, similarity_top_k=100)
    all_nodes = [n.node for n in dummy.retrieve(QUERY)]
nodes_list = list(all_nodes)

bm25 = BM25Retriever.from_defaults(
    nodes=nodes_list,
    tokenizer=lambda t: list(jieba.cut(t)),
    similarity_top_k=TOP_K,
)
bm25_nodes = bm25.retrieve(QUERY)

print(f"  jieba 分词 \"{QUERY}\" → {list(jieba.cut(QUERY))}")
for i, n in enumerate(bm25_nodes):
    is_a1 = "A1" in n.text[:20] or "金融风险管理关注" in n.text[:40]
    marker = " ← ★ A1!" if is_a1 else ""
    print(f"  [{i+1}] {marker}  {n.text.strip()[:60]}...")

# ── 5. Step 4: RRF 融合排名 ──────────────────────
print(f"\n【Step 4】RRF 融合 (k=60, top_k={TOP_K})")
print("-" * 70)

rrf_results = _rrf_fusion(vec_filtered, bm25_nodes, top_k=TOP_K)
print(f"  RRF 融合后: {len(rrf_results)} 个结果")
for i, n in enumerate(rrf_results):
    is_a1 = "A1" in n.text[:20] or "金融风险管理关注" in n.text[:40]
    marker = " ← ★ A1!" if is_a1 else ""
    # 计算 RRF 来源
    vec_rank = None
    bm25_rank = None
    vec_texts = [x.text.strip()[:80] for x in vec_filtered]
    bm25_texts = [x.text.strip()[:80] for x in bm25_nodes]
    n_text_sig = n.text.strip()[:80]
    if n_text_sig in vec_texts:
        vec_rank = vec_texts.index(n_text_sig) + 1
    if n_text_sig in bm25_texts:
        bm25_rank = bm25_texts.index(n_text_sig) + 1
    source_info = f"vec#{vec_rank}" if vec_rank else ""
    if bm25_rank:
        source_info += f"+bm25#{bm25_rank}" if source_info else f"bm25#{bm25_rank}"
    print(f"  [{i+1:2d}] rrf_score={n.score:.4f}  [{source_info}]{marker}  {n.text.strip()[:60]}...")

# ── 6. Step 5: Reranker 最终评分 ──────────────────
print(f"\n【Step 5】SentenceTransformerRerank 最终评分 (top_n=8)")
print("-" * 70)

candidates = [NodeWithScore(node=TextNode(text=n.text), score=0.0) for n in rrf_results]
reranker = SentenceTransformerRerank(top_n=8)
bundle = QueryBundle(query_str=QUERY)
reranked = reranker.postprocess_nodes(candidates, query_bundle=bundle)

rerank_positions = {}
for i, n in enumerate(reranked):
    is_a1 = "A1" in n.text[:20] or "金融风险管理关注" in n.text[:40]
    marker = " ← ★ A1!" if is_a1 else ""
    # 计算 embedding 原始排名
    text_sig = n.text.strip().replace(chr(65279), "")
    embed_rank = next(
        (r["rank"] for r in embedding_rank
         if r["text"].replace(chr(65279), "").strip()[:60] == text_sig[:60]),
        "N/A"
    )
    # 计算 RRF 排名
    rrf_rank = next(
        (idx + 1 for idx, r in enumerate(rrf_results)
         if r.text.strip()[:60] == n.text.strip()[:60]),
        "N/A"
    )
    print(f"  [{i+1}] rerank_score={n.score:.4f}  "
          f"(embed_rank=#{embed_rank}, rrf_rank=#{rrf_rank}){marker}")
    print(f"        text_len={len(n.text.strip())}  {n.text.strip()[:60]}...")
    rerank_positions[n.text.strip()[:60]] = {
        "rerank_rank": i + 1,
        "rerank_score": round(float(n.score), 4),
        "embed_rank": embed_rank,
        "rrf_rank": rrf_rank,
    }

# ── 7. A1 专项对比 ──────────────────────────────
print(f"\n{'=' * 70}")
print(f"★ A1 全链路评分对比")
print(f"{'=' * 70}")

# A1 在 embedding 中的信息
a1_text_sig = a1_embed["text"].replace(chr(65279), "").strip()[:60]

# A1 在 RRF 中的排名
a1_rrf_rank = next(
    (idx + 1 for idx, r in enumerate(rrf_results)
     if r.text.strip()[:60] == a1_text_sig),
    "未进入 RRF"
)

# A1 在 reranker 中的排名
a1_rerank = rerank_positions.get(a1_text_sig, None)

print(f"  Stage 1 — ChromaDB embedding: ")
print(f"    cosine_similarity: {a1_embed['cosine_sim']:.4f}")
print(f"    embedding 排名:     #{a1_embed['rank']}/{vector_count}")
print(f"")
print(f"  Stage 2 — VectorIndexRetriever + threshold=0.2:")
a1_in_vec = next((i+1 for i, n in enumerate(vec_filtered) if n.text.strip()[:60] == a1_text_sig), None)
print(f"    通过阈值? {'是 (排名 #' + str(a1_in_vec) + ')' if a1_in_vec else '否 (被过滤)'}")
print(f"")
print(f"  Stage 3 — BM25 (jieba 分词):")
a1_in_bm25 = next((i+1 for i, n in enumerate(bm25_nodes) if n.text.strip()[:60] == a1_text_sig), None)
print(f"    BM25 命中? {'是 (排名 #' + str(a1_in_bm25) + ')' if a1_in_bm25 else '否'}")
print(f"")
print(f"  Stage 4 — RRF 融合:")
print(f"    RRF 排名: {a1_rrf_rank}")
print(f"")
print(f"  Stage 5 — Reranker 最终:")
if a1_rerank:
    print(f"    Reranker 排名:    #{a1_rerank['rerank_rank']}")
    print(f"    Reranker score:   {a1_rerank['rerank_score']:.4f}")
else:
    print(f"    未进入 reranker top-8")
print(f"")
print(f"  【关键对比】embedding sim → reranker score:")
print(f"    cosine_sim={a1_embed['cosine_sim']:.4f}  →  rerank_score={a1_rerank['rerank_score'] if a1_rerank else 'N/A':.4f}")
print(f"    排名变化: embedding #{a1_embed['rank']} → reranker #{a1_rerank['rerank_rank'] if a1_rerank else 'N/A'}")

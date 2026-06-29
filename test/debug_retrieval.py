"""
调试脚本 v3：RAG 检索管线诊断
1. ChromaDB 重复条目分析
2. Cosine 相似度分布与 A1 排名
3. 0.6 阈值影响评估
4. Chunk 重叠分析
5. BOM 污染源追踪
6. Reranker 评分链验证
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import chromadb
from llama_index.core import VectorStoreIndex, QueryBundle, Settings
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.schema import NodeWithScore, TextNode
from config.init import init_models
from app.modules.kb_manager import KnowledgeBase
from app.modules.kb_manager.chunker import chunk_documents

init_models()
_kb = KnowledgeBase()
KB_NAME = "062500"
QUERY = "A1是什么"
CWD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 1. ChromaDB 加载 ──────────────────────────────
db = chromadb.PersistentClient(path=_kb.vector_db_path(KB_NAME))
chroma_collection = db.get_collection("kb_index")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
vector_count = chroma_collection.count()
print(f"ChromaDB 向量总数: {vector_count}")
print("=" * 60)

# ── 2. ChromaDB 完整查询 ───────────────────────────
print(f"\n[1] ChromaDB 全量查询 \"{QUERY}\" (48条):")
query_embedding = Settings.embed_model.get_text_embedding(QUERY)
raw_results = chroma_collection.query(
    query_embeddings=[query_embedding],
    n_results=48,
    include=["documents", "distances", "metadatas"]
)

# 统计唯一 + 重复
seen_texts = set()
unique_list = []
dup_list = []
for i, (doc, dist) in enumerate(zip(raw_results["documents"][0], raw_results["distances"][0])):
    score = round(1 - dist, 4)
    text_sig = doc[:100]
    entry = (i+1, score, doc.replace("\n", " ")[:70])
    if text_sig in seen_texts:
        dup_list.append(entry)
    else:
        seen_texts.add(text_sig)
        unique_list.append(entry)

print(f"  唯一内容: {len(unique_list)} 条")
print(f"  重复内容: {len(dup_list)} 条")

# 显示唯一结果
print(f"\n  唯一结果排序:")
first_a1 = None
for rank, (pos, score, clip) in enumerate(unique_list):
    is_a1 = "A1" in clip[:20] or "金融风险管理关注" in clip[:40]
    marker = " ← ★ A1!" if is_a1 else ""
    if is_a1 and first_a1 is None:
        first_a1 = rank
    print(f"    #{rank+1:2d} (orig#{pos}) cosine_sim={score:.4f}  {clip}...{marker}")

if first_a1 is not None:
    print(f"\n  A1 在唯一结果中排名: 第 {first_a1+1}/{len(unique_list)}")
else:
    print(f"\n  A1 未在 top-48 中出现!")

# ── 3. 0.6 阈值影响 ───────────────────────────────
print(f"\n[2] 0.6 阈值影响分析:")
vec_retriever = VectorIndexRetriever(index=index, similarity_top_k=8)
raw_nodes = vec_retriever.retrieve(QUERY)
for n in raw_nodes:
    print(f"  VectorIndexRetriever score={n.score:.4f}")
print(f"  → 最大值: {max(n.score or 0 for n in raw_nodes):.4f}")
print(f"  → 全部 < 0.6, 向量路径将被完全清空!")

# ── 4. 源文件分析 ──────────────────────────────────
print(f"\n[3] 源文件→分块 分析:")
rag_dir = os.path.join(CWD, "kb/062500/files/rag-test")
from llama_index.core import Document
docs = []
for root, _, files in os.walk(rag_dir):
    for fname in files:
        if fname.endswith(".txt"):
            fpath = os.path.join(root, fname)
            with open(fpath, "r", encoding="utf-8-sig") as f:
                text = f.read()
            docs.append(Document(text=text, metadata={"file_path": fpath}))
print(f"  源文件 -> {len(docs)} 个 Document")

nodes = chunk_documents(docs)
print(f"  Document -> {len(nodes)} 个 chunk")
print(f"  期望向量数: {len(nodes)}, 实际向量数: {vector_count}")
if vector_count > len(nodes):
    print(f"  多出 {vector_count - len(nodes)} 个 = 索引了 {1 + (vector_count - len(nodes)) // len(nodes)} 次")

# ── 5. 重叠分析 ──────────────────────────────────
print(f"\n[4] Chunk 重叠分析:")
# 按 A 文件的序号的 chunk 分布
for section in ["A1", "A2", "A3", "A4", "B1", "C1", "D1"]:
    matches = [n for n in nodes if section in n.text[:20]]
    print(f"  含 \"{section}\" 的 chunk 数: {len(matches)}")
    for m in matches:
        print(f"    id={m.node_id[:16]}... len={len(m.text.strip())}")
        if len(matches) > 1:
            # 显示相邻 chunk 的文本边界
            idx = nodes.index(m)
            if idx > 0:
                prev_end = nodes[idx-1].text.strip()[-60:].replace("\n", " ")
                this_start = m.text.strip()[:60].replace("\n", " ")
                overlap_chars = len(set(m.text.strip()[:128]) & set(nodes[idx-1].text.strip()[-128:]))
                print(f"      ← 与前 chunk overlap ~{overlap_chars} 字符")
                print(f"      前 chunk 尾部: ...{prev_end}")
                print(f"      本 chunk 头部: {this_start}")

# ── 6. BOM 追踪 ───────────────────────────────────
print(f"\n[5] BOM 污染追踪:")
# 检查源文件
for root, _, files in os.walk(os.path.join(CWD, "kb/062500/files/")):
    for fname in files:
        fpath = os.path.join(root, fname)
        with open(fpath, "rb") as f:
            raw = f.read(4)
        has_bom = raw[:3] == b'\xef\xbb\xbf'
        if has_bom:
            print(f"  源文件含 BOM: {fpath}")
            # 检查 chunk 中 BOM 分布
            bom_in_nodes = sum(1 for n in nodes if "﻿" in n.text and os.path.basename(fpath).replace(".txt","") in str(n.metadata))
            print(f"    对应 chunk 中带 BOM 的: {bom_in_nodes} 个")

bom_total = sum(1 for n in nodes if "﻿" in n.text)
print(f"  共 {bom_total}/{len(nodes)} 个 chunk 含 BOM 字符")

# ── 7. Reranker 评分链 ──────────────────────────
print(f"\n[6] Reranker 评分模拟 (top-15 ChromaDB 候选):")
top_texts = raw_results["documents"][0][:15]
candidates = [NodeWithScore(node=TextNode(text=t), score=0.0) for t in top_texts]
bundle = QueryBundle(query_str=QUERY)
reranker = SentenceTransformerRerank(top_n=5)
reranked = reranker.postprocess_nodes(candidates, query_bundle=bundle)

for i, n in enumerate(reranked):
    score = round(float(n.score), 4)
    clip = n.text.strip()[:60].replace("\n", " ")
    is_a1 = "A1" in n.text[:20] or "金融风险管理关注" in n.text[:40]
    marker = " ← ★ A1!" if is_a1 else ""
    print(f"  [{i+1}] rerank_score={score:.4f}  {clip}...{marker}")

# ── 8. 500 字符不截断模拟 ──────────────────────
print(f"\n[7] 测试: 若 top_n=8 且不截断 300 字符:")
reranker8 = SentenceTransformerRerank(top_n=8)
reranked8 = reranker8.postprocess_nodes(candidates, query_bundle=bundle)
for i, n in enumerate(reranked8):
    score = round(float(n.score), 4)
    is_a1 = "A1" in n.text[:20] or "金融风险管理关注" in n.text[:40]
    marker = " ← ★ A1!" if is_a1 else ""
    print(f"  [{i+1}] rerank_score={score:.4f}  text_len={len(n.text.strip())}{marker}")

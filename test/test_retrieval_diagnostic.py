"""
检索管线分阶段诊断工具。

对指定知识库执行查询，输出 ChromaDB → VectorIndexRetriever → BM25 → RRF → Reranker
各阶段的评分、排名，自动检测异常模式。

用法:
    python test/test_retrieval_diagnostic.py <kb_name> "<query>"
    python test/test_retrieval_diagnostic.py <kb_name> "<query>" --top-k 16 --top-n 8 --threshold 0.1
    python test/test_retrieval_diagnostic.py <kb_name> "<query>" --output-dir tmp/diag

输出:
    - 终端: 分阶段排名表 + 异常告警
    - JSON: test/diagnostic_output/<kb_name>_<timestamp>.json
"""
import sys, os, json, argparse, subprocess
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 解析参数 ──────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="检索管线分阶段诊断工具")
    p.add_argument("kb_name", help="知识库名称")
    p.add_argument("query", help="查询内容")
    p.add_argument("--top-k", type=int, default=12, help="Vector/BM25/RRF 召回数 (default: 12)")
    p.add_argument("--top-n", type=int, default=8, help="Reranker 保留数 (default: 8)")
    p.add_argument("--threshold", type=float, default=0.2, help="分数阈值 (default: 0.2)")
    p.add_argument("--output-dir", default=None, help="JSON 输出目录 (default: test/diagnostic_output/)")
    return p.parse_args()


# ── 阶段 1: ChromaDB 全量查询 ─────────────────────
def stage1_chromadb(kb_name, query, embed_model, chroma_collection):
    """ChromaDB 余弦相似度排名 + 重复检测。"""
    query_emb = embed_model.get_text_embedding(query)
    n_total = chroma_collection.count()
    results = chroma_collection.query(
        query_embeddings=[query_emb],
        n_results=max(n_total, 1),
        include=["documents", "distances", "metadatas"],
    )

    entries = []
    seen_sigs = set()
    dup_count = 0
    for i, (doc, dist) in enumerate(zip(results["documents"][0], results["distances"][0])):
        cosine_sim = round(1 - dist, 4)
        sig = doc[:80]
        is_dup = sig in seen_sigs
        if is_dup:
            dup_count += 1
        else:
            seen_sigs.add(sig)
        text_clean = doc.replace("﻿", "")
        entries.append({
            "rank": i + 1,
            "cosine_sim": cosine_sim,
            "text": text_clean,
            "is_duplicate": is_dup,
        })

    dup_rate = round(dup_count / max(len(entries), 1) * 100, 1)
    all_negative = all(e["cosine_sim"] < 0 for e in entries)

    return entries, {"dup_rate": dup_rate, "all_negative": all_negative, "total": n_total}


# ── 阶段 2: VectorIndexRetriever ──────────────────
def stage2_vector(kb_name, query, index, top_k, threshold):
    """向量检索 + 阈值过滤。"""
    from llama_index.core.retrievers import VectorIndexRetriever
    from app.modules.retrieval.retriever import _ScoreThresholdRetriever

    vec_retriever = VectorIndexRetriever(index=index, similarity_top_k=top_k)
    threshold_retriever = _ScoreThresholdRetriever(vec_retriever, threshold=threshold)
    from llama_index.core import QueryBundle
    bundle = QueryBundle(query_str=query)

    raw = vec_retriever.retrieve(bundle)
    filtered = threshold_retriever.retrieve(bundle)

    raw_entries = []
    for i, n in enumerate(raw):
        raw_entries.append({
            "rank": i + 1,
            "score": round(float(n.score), 4) if n.score else None,
            "text": n.text.strip().replace("﻿", ""),
        })

    filter_rate = round((len(raw) - len(filtered)) / max(len(raw), 1) * 100, 1)

    filtered_entries = []
    for i, n in enumerate(filtered):
        filtered_entries.append({
            "rank": i + 1,
            "score": round(float(n.score), 4) if n.score else None,
            "text": n.text.strip().replace("﻿", ""),
        })

    return raw_entries, filtered_entries, filter_rate, filtered


# ── 阶段 3: BM25 ──────────────────────────────────
def stage3_bm25(query, index, top_k):
    """BM25 检索。"""
    import jieba
    from llama_index.core.retrievers import VectorIndexRetriever
    from llama_index.retrievers.bm25 import BM25Retriever

    tokens = list(jieba.cut(query))

    all_nodes = list(index.docstore.docs.values()) if hasattr(index, 'docstore') else []
    if not all_nodes:
        dummy = VectorIndexRetriever(index=index, similarity_top_k=100)
        all_nodes = [n.node for n in dummy.retrieve(query)]

    bm25 = BM25Retriever.from_defaults(
        nodes=list(all_nodes),
        tokenizer=lambda t: list(jieba.cut(t)),
        similarity_top_k=top_k,
    )
    bm25_nodes = bm25.retrieve(query)

    entries = []
    for i, n in enumerate(bm25_nodes):
        entries.append({
            "rank": i + 1,
            "text": n.text.strip().replace("﻿", ""),
        })

    return entries, tokens, bm25_nodes


# ── 阶段 4: RRF 融合 ──────────────────────────────
def stage4_rrf(vec_raw_nodes, bm25_raw_nodes, top_k):
    """RRF 融合 + 来源标注。"""
    from app.modules.retrieval.retriever import _rrf_fusion

    rrf_results = _rrf_fusion(vec_raw_nodes, bm25_raw_nodes, top_k=top_k)

    entries = []
    for i, n in enumerate(rrf_results):
        # 溯源
        n_sig = n.text.strip()[:80]
        vec_rank = None
        for j, v in enumerate(vec_raw_nodes):
            if v.text.strip()[:80] == n_sig:
                vec_rank = j + 1
                break
        bm25_rank = None
        for j, v in enumerate(bm25_raw_nodes):
            if v.text.strip()[:80] == n_sig:
                bm25_rank = j + 1
                break

        source = ""
        if vec_rank:
            source += f"vec#{vec_rank}"
        if bm25_rank:
            source += f"+bm25#{bm25_rank}" if source else f"bm25#{bm25_rank}"
        if not source:
            source = "unknown"

        entries.append({
            "rank": i + 1,
            "rrf_score": round(float(n.score), 4) if n.score else None,
            "source": source,
            "text": n.text.strip().replace("﻿", ""),
        })

    return entries, rrf_results


# ── 阶段 5: Reranker ──────────────────────────────
def stage5_reranker(rrf_raw_nodes, rrf_entries, query, top_n, chromadb_entries):
    """Reranker 最终评分 + 排名对比。"""
    from llama_index.core import QueryBundle
    from llama_index.core.postprocessor import SentenceTransformerRerank

    reranker = SentenceTransformerRerank(top_n=top_n)
    reranked = reranker.postprocess_nodes(rrf_raw_nodes, query_bundle=QueryBundle(query_str=query))

    entries = []
    for i, n in enumerate(reranked):
        text_sig = n.text.strip().replace("﻿", "")[:80]

        # 查 embedding 原始排名
        embed_rank = next(
            (e["rank"] for e in chromadb_entries if e["text"][:80] == text_sig), None)

        # 查 RRF 排名
        rrf_rank = next(
            (e["rank"] for e in rrf_entries if e["text"][:80] == text_sig), None)

        entries.append({
            "rank": i + 1,
            "rerank_score": round(float(n.score), 4) if n.score else None,
            "embed_rank": embed_rank,
            "rrf_rank": rrf_rank,
            "text": n.text.strip().replace("﻿", ""),
        })

    return entries


# ── 异常诊断引擎 ─────────────────────────────────
def diagnose(args, chromadb_info, chromadb_entries, filter_rate, reranker_entries):
    warnings = []

    # E01: cosine_sim 全负数
    if chromadb_info["all_negative"]:
        warnings.append({
            "code": "E01",
            "severity": "WARN",
            "message": f"All {chromadb_info['total']} cosine_sim values are negative "
                       f"— embedding model may be incompatible with this query domain",
        })

    # E02: 阈值过滤率过高
    if filter_rate > 50:
        warnings.append({
            "code": "E02",
            "severity": "WARN",
            "message": f"Threshold filtering {filter_rate}% of results (>50%) "
                       f"— threshold ({args.threshold}) may be too high",
        })

    # E03: 重复率过高
    if chromadb_info["dup_rate"] > 10:
        warnings.append({
            "code": "E03",
            "severity": "ERROR",
            "message": f"Duplicate rate: {chromadb_info['dup_rate']}% (>10%) "
                       f"— index is not idempotent, re-index required",
        })

    # E04: 含查询关键词的片段排名低于中位数
    query_keywords = set(args.query.lower().split())
    if reranker_entries:
        mid = len(reranker_entries) // 2
        for e in reranker_entries:
            text_lower = e["text"].lower()
            if any(kw in text_lower for kw in query_keywords):
                if e["rank"] > mid:
                    warnings.append({
                        "code": "E04",
                        "severity": "INFO",
                        "message": f"Query keyword match found at reranker #{e['rank']} (below median #{mid}) "
                                   f"— chunk strategy or embedding may need tuning",
                    })
                    break

    # E05: Reranker vs embedding 排名严重分歧
    for e in reranker_entries:
        if e.get("embed_rank") and e.get("rank"):
            diff = abs(e["embed_rank"] - e["rank"])
            if diff > max(chromadb_info["total"] * 0.5, 3):
                warnings.append({
                    "code": "E05",
                    "severity": "INFO",
                    "message": f"Large ranking gap: embed #{e['embed_rank']} → reranker #{e['rank']} "
                               f"(diff={diff}) — bi-encoder vs cross-encoder strongly disagree on '{e['text'][:40]}...'",
                })
                break

    return warnings


# ── 输出格式化 ────────────────────────────────────
def print_stage_header(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")

def print_stage_entries(entries, key_label, extra_fields=None):
    if extra_fields is None:
        extra_fields = {}
    for e in entries:
        vals = [f"#{e['rank']:2d}"]
        for k, label in extra_fields.items():
            v = e.get(k)
            if v is not None:
                vals.append(f"{label}={v}")
        clip = e["text"][:70].replace("\n", " ")
        keyword_match = any(kw in clip.lower() for kw in ["a1", "金融风险管理"])
        marker = " ← ★" if keyword_match else ""
        print(f"  [{' '.join(vals)}]  {clip}{marker}")

def print_warnings(warnings):
    if warnings:
        print(f"\n{'!' * 70}")
        print(f"  异常诊断报告")
        print(f"{'!' * 70}")
        for w in warnings:
            icon = {"WARN": "⚠️", "ERROR": "🚫", "INFO": "ℹ️"}.get(w["severity"], "•")
            print(f"  {icon} [{w['code']}] {w['message']}")
    else:
        print(f"\n  ✅ 未检测到异常")


# ── 主流程 ────────────────────────────────────────
def main():
    args = parse_args()

    # 初始化
    from config.init import init_models
    from llama_index.core import Settings
    from app.modules.kb_manager import KnowledgeBase
    import chromadb
    from llama_index.core import VectorStoreIndex
    from llama_index.vector_stores.chroma import ChromaVectorStore

    init_models()
    _kb = KnowledgeBase()

    kb_path = _kb.vector_db_path(args.kb_name)
    if not os.path.isdir(kb_path):
        print(f"[ERROR] 知识库 '{args.kb_name}' 不存在或无向量数据")
        sys.exit(1)

    db = chromadb.PersistentClient(path=kb_path)
    chroma_collection = db.get_collection("kb_index")
    index = VectorStoreIndex.from_vector_store(
        vector_store=ChromaVectorStore(chroma_collection=chroma_collection)
    )

    print(f"\n  知识库: {args.kb_name}")
    print(f"  查询:   \"{args.query}\"")
    print(f"  配置:   --top-k {args.top_k}  --top-n {args.top_n}  --threshold {args.threshold}")
    print(f"  时间:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ── Stage 1 ──
    print_stage_header("Stage 1: ChromaDB Embedding 空间")
    chromadb_entries, chromadb_info = stage1_chromadb(
        args.kb_name, args.query, Settings.embed_model, chroma_collection)
    print(f"  向量总数: {chromadb_info['total']}  |  重复率: {chromadb_info['dup_rate']}%")
    print_stage_entries(chromadb_entries, "cosine_sim",
                        {"cosine_sim": ""})

    # ── Stage 2 ──
    print_stage_header("Stage 2: VectorIndexRetriever")
    vec_raw, vec_filtered, filter_rate, vec_raw_nodes = stage2_vector(
        args.kb_name, args.query, index, args.top_k, args.threshold)
    print(f"  原始 {len(vec_raw)} 条 → 过滤后 {len(vec_filtered)} 条 (过滤率 {filter_rate}%)")
    print_stage_entries(vec_filtered, "score", {"score": ""})

    # ── Stage 3 ──
    print_stage_header("Stage 3: BM25 检索")
    bm25_entries, tokens, bm25_raw_nodes = stage3_bm25(args.query, index, args.top_k)
    print(f"  分词: {tokens}")
    print_stage_entries(bm25_entries, "", {})

    # ── Stage 4 ──
    print_stage_header("Stage 4: RRF 融合")
    rrf_entries, rrf_raw_nodes = stage4_rrf(vec_raw_nodes, bm25_raw_nodes, args.top_k)
    print_stage_entries(rrf_entries, "rrf_score",
                        {"rrf_score": "", "source": ""})

    # ── Stage 5 ──
    print_stage_header("Stage 5: Reranker 最终排名")
    reranker_entries = stage5_reranker(
        rrf_raw_nodes, rrf_entries, args.query, args.top_n, chromadb_entries)
    print_stage_entries(reranker_entries, "rerank_score",
                        {"rerank_score": "", "embed_rank": "embed#", "rrf_rank": "rrf#"})

    # ── 诊断 ──
    warnings = diagnose(args, chromadb_info, chromadb_entries, filter_rate, reranker_entries)
    print_warnings(warnings)

    # ── JSON 输出 ──
    output = {
        "config": {"kb_name": args.kb_name, "query": args.query,
                    "top_k": args.top_k, "top_n": args.top_n, "threshold": args.threshold},
        "timestamp": datetime.now().isoformat(),
        "stages": {
            "chromadb": {"total": chromadb_info["total"], "dup_rate": chromadb_info["dup_rate"],
                         "all_negative": chromadb_info["all_negative"], "entries": chromadb_entries},
            "vector": {"raw_count": len(vec_raw), "filtered_count": len(vec_filtered),
                       "filter_rate": filter_rate, "entries": vec_filtered},
            "bm25": {"tokens": tokens, "entries": bm25_entries},
            "rrf": {"entries": rrf_entries},
            "reranker": {"entries": reranker_entries},
        },
        "warnings": warnings,
    }

    output_dir = args.output_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "diagnostic_output")
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(output_dir, f"{args.kb_name}_{ts}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  📄 JSON 报告: {out_path}")


if __name__ == "__main__":
    main()

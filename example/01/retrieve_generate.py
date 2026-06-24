"""
retrieve_generate.py — RAG Part 2: 检索 + 生成
===============================================
流程：用户问题 -> Embedding -> ChromaDB 检索 -> 构建 RAG Prompt -> LLM 生成 -> 回答+来源

用法：
    python retrieve_generate.py <问题>
    python retrieve_generate.py "什么是RAG？"
"""

import os
import sys
import json
import requests

# -- 配置 ---------------------------------------------------
OLLAMA_URL = "http://127.0.0.1:11434"
EMBED_MODEL = "qwen3-embedding:4b"      # 检索用的 Embedding 模型
LLM_MODEL = "qwen3.5:9b"               # 生成用的 LLM 模型
TOP_K = 5                                # 检索返回的最相关结果数
DB_PATH = os.path.join(os.path.dirname(__file__), "rag_demo_db")
# ----------------------------------------------------------


# -- 1. Embedding（查询向量化）-------------------------------

def embed_query(text: str) -> list[float]:
    """将查询文本转为向量（单条）"""
    url = f"{OLLAMA_URL}/api/embed"
    payload = {
        "model": EMBED_MODEL,
        "input": [text],
    }
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    embeddings = data.get("embeddings", [])
    if not embeddings:
        raise RuntimeError("Embedding API 返回空结果")
    return embeddings[0]


# -- 2. ChromaDB 检索 ---------------------------------------

def retrieve(query_vector: list[float], top_k: int = TOP_K) -> list[dict]:
    """在 ChromaDB 中检索最相似的文本块"""
    import chromadb

    if not os.path.exists(DB_PATH):
        return None  # 数据库不存在

    client = chromadb.PersistentClient(path=DB_PATH)

    try:
        collection = client.get_collection("rag_demo")
    except Exception:
        return None  # 集合不存在

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection.count()),
        include=["documents", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]

    # ChromaDB 用 cosine 距离，转为相似度分数（0~1，越大越相关）
    return [
        {
            "text": doc,
            "score": round(1 - dist, 4),
        }
        for doc, dist in zip(documents, distances)
    ]


# -- 3. RAG Prompt ------------------------------------------

RAG_SYSTEM_PROMPT = """你是一个基于文档内容回答问题的助手。

请遵循以下规则：
1. 仅根据上面提供的"参考文档片段"来回答问题
2. 如果参考片段不足以回答问题，请明确说明"根据提供的文档无法回答"
3. 引用具体信息时，标注对应的来源编号 [来源 1]、[来源 2] 等
4. 回答要简洁、准确、有条理
5. 使用中文回答"""


def build_rag_prompt(query: str, contexts: list[dict]) -> list[dict]:
    """构建 RAG 对话消息"""
    context_text = "\n\n".join(
        f"[来源 {i+1}] {ctx['text']}"
        for i, ctx in enumerate(contexts)
    )

    user_message = f"""参考文档片段：
{context_text}

---

问题：{query}

请基于以上参考文档片段回答我的问题。"""

    return [
        {"role": "system", "content": RAG_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


# -- 4. LLM 生成 --------------------------------------------

def generate_answer(messages: list[dict]) -> str:
    """调用 Ollama Chat API 生成回答"""
    url = f"{OLLAMA_URL}/api/chat"
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.3,    # 低温度，更精确
        },
    }
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"]


# -- 主流程 ------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("用法: python retrieve_generate.py <问题>")
        print("示例: python retrieve_generate.py \"什么是RAG？\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    print(f"\n{'='*50}")
    print(f"RAG 检索流程 -- Part 2: 检索 + 生成")
    print(f"{'='*50}\n")

    print(f"问题: {query}\n")

    # Step 1: 查询向量化
    print(f"[1/3] 查询向量化 (模型: {EMBED_MODEL})")
    query_vector = embed_query(query)
    print(f"      [OK] 向量维度: {len(query_vector)}\n")

    # Step 2: 检索
    print(f"[2/3] 语义检索 (Top-{TOP_K})")
    results = retrieve(query_vector)

    if results is None:
        print("[ERROR] 未找到索引数据。请先运行: python parse_index.py <文档路径>")
        sys.exit(1)

    print(f"      [OK] 检索到 {len(results)} 个相关片段\n")

    for i, r in enumerate(results):
        preview = r["text"][:80].replace("\n", " ")
        print(f"      [来源 {i+1}] 相似度: {r['score']:.4f}")
        print(f"              内容: {preview}...")
    print()

    # Step 3: 生成
    print(f"[3/3] LLM 生成回答 (模型: {LLM_MODEL})")
    messages = build_rag_prompt(query, results)
    answer = generate_answer(messages)
    print(f"      [OK] 生成完成\n")

    print(f"{'='*50}")
    print(f"回答")
    print(f"{'='*50}")
    print(answer)
    print(f"\n{'='*50}")
    print(f"参考来源")
    print(f"{'='*50}")
    for i, r in enumerate(results):
        print(f"\n[来源 {i+1}] (相似度: {r['score']:.4f})")
        print("-" * 40)
        print(r["text"].strip())
    print()


if __name__ == "__main__":
    main()

"""
retrieve_generate.py — 使用 LlamaIndex 实现：检索 + 生成
=========================================================
流程：用户问题 -> QueryEngine -> 检索相关片段 -> LLM 生成 -> 回答+来源

对比 01/ 的纯手写版，llama_index 自动处理了：
  - 查询向量化
  - ChromaDB 检索与排序
  - RAG Prompt 的构建
  - LLM 调用与结果解析

用法：
    python retrieve_generate.py <问题>
    python retrieve_generate.py "什么是RAG？"
"""

import os
import sys

import chromadb
from llama_index.core import (
    VectorStoreIndex,
    Settings,
)
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore


# -- 配置 ---------------------------------------------------
OLLAMA_URL = "http://127.0.0.1:11434"
EMBED_MODEL = "qwen3-embedding:4b"      # 检索用
LLM_MODEL = "qwen3.5:9b"               # 生成用
TOP_K = 5
DB_PATH = os.path.join(os.path.dirname(__file__), "rag_demo_db_llama")
# ----------------------------------------------------------


def main():
    if len(sys.argv) < 2:
        print("用法: python retrieve_generate.py <问题>")
        print("示例: python retrieve_generate.py \"什么是RAG？\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])

    print(f"\n{'='*50}")
    print(f"LlamaIndex -- Part 2: 检索 + 生成")
    print(f"{'='*50}\n")

    print(f"问题: {query}\n")

    # 1. 检查 ChromaDB 是否存在
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] 未找到索引数据（{DB_PATH}）")
        print("请先运行: python parse_index.py <文档路径>")
        sys.exit(1)

    # 2. 配置全局模型
    print(f"[配置] Embedding: {EMBED_MODEL} | LLM: {LLM_MODEL}")
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=OLLAMA_URL,
    )
    Settings.llm = Ollama(
        model=LLM_MODEL,
        base_url=OLLAMA_URL,
        temperature=0.3,
        request_timeout=60,
    )

    # 3. 从 ChromaDB 加载已有索引
    #
    #    llama_index 的妙处：之前存的向量 + 文档，
    #    只要指定同一个 ChromaDB 集合，就能恢复出完整的 Index 对象
    print(f"[1/3] 加载向量索引...")
    db = chromadb.PersistentClient(path=DB_PATH)
    chroma_collection = db.get_collection("rag_demo")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
    print(f"      [OK] 索引加载完成（共 {chroma_collection.count()} 个向量）\n")

    # 4. 创建 Query Engine 并检索
    #
    #    as_query_engine() 封装了整个 RAG 流程：
    #    query -> embed -> 检索 top-k -> 构建 prompt -> LLM -> 返回
    print(f"[2/3] 检索 + 生成 (Top-{TOP_K})")
    query_engine = index.as_query_engine(
        similarity_top_k=TOP_K,
    )

    # 5. 执行查询
    response = query_engine.query(query)
    print(f"      [OK] 生成完成\n")

    # 6. 输出回答
    print(f"{'='*50}")
    print(f"回答")
    print(f"{'='*50}")
    print(response)
    print()

    # 7. 输出参考来源
    print(f"{'='*50}")
    print(f"参考来源")
    print(f"{'='*50}")

    if hasattr(response, "source_nodes") and response.source_nodes:
        for i, node in enumerate(response.source_nodes):
            score = node.score if hasattr(node, "score") else "N/A"
            print(f"\n[来源 {i+1}] (相似度: {score:.4f})" if isinstance(score, float)
                  else f"\n[来源 {i+1}]")
            print("-" * 40)
            print(node.text.strip()[:300])
            print("..." if len(node.text) > 300 else "")
    print()


if __name__ == "__main__":
    main()

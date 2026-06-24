"""
test_retrieve.py — 知识库检索测试接口。

用法：
    python test/test_retrieve.py <知识库名称> "<查询内容>"

示例：
    python test/test_retrieve.py my-docs "这个文档讲了什么？"

注意：此脚本为测试用途，归档 change 时删除。
"""

import os
import sys

# 确保项目根目录在 Python 路径中
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.chroma import ChromaVectorStore

from config.settings import EMBED_MODEL, LLM_MODEL, KB_ROOT
from config.init import init_models


# ── RAG Prompt ────────────────────────────────

RAG_SYSTEM_PROMPT = """你是一个基于文档内容回答问题的助手。

规则：
1. 仅根据上面提供的"参考文档片段"来回答问题
2. 如果参考片段不足以回答问题，请说明"根据提供的文档无法回答"
3. 引用具体信息时，标注对应的来源编号 [来源 1]、[来源 2] 等
4. 回答要简洁、准确、有条理
5. 使用中文回答"""


def main():
    if len(sys.argv) < 3:
        print("用法: python test/test_retrieve.py <知识库名称> \"<查询内容>\"")
        print("示例: python test/test_retrieve.py my-docs \"这个文档讲了什么？\"")
        sys.exit(1)

    kb_name = sys.argv[1]
    query = sys.argv[2]

    kb_path = os.path.join(KB_ROOT, kb_name)
    vector_db_path = os.path.join(kb_path, "vector_db")

    # 检查知识库是否存在
    if not os.path.isdir(kb_path):
        print(f"[ERROR] 知识库 '{kb_name}' 不存在。请先创建并上传文件。")
        print(f"        python -m app.modules.kb_manager.cli kb create {kb_name}")
        print(f"        python -m app.modules.kb_manager.cli kb upload {kb_name} <文件路径>")
        sys.exit(1)

    if not os.path.isdir(vector_db_path):
        print(f"[ERROR] 知识库 '{kb_name}' 中暂无向量数据。请先上传文件。")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"知识库检索测试: {kb_name}")
    print(f"{'='*50}\n")
    print(f"问题: {query}\n")

    # 1. 配置模型（全局初始化）
    print(f"[配置] Embedding: {EMBED_MODEL} | LLM: {LLM_MODEL}")
    init_models()

    # 2. 加载 ChromaDB
    db = chromadb.PersistentClient(path=vector_db_path)
    try:
        chroma_collection = db.get_collection("kb_index")
    except Exception:
        print(f"[ERROR] 知识库 '{kb_name}' 中未找到索引数据。请先上传文件。")
        sys.exit(1)

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    vector_count = chroma_collection.count()
    print(f"[数据] 加载了 {vector_count} 个向量\n")

    if vector_count == 0:
        print("[ERROR] 知识库中没有向量数据。请先上传文件。")
        sys.exit(1)

    # 3. 检索 + 生成
    query_engine = index.as_query_engine(
        similarity_top_k=5,
    )
    response = query_engine.query(query)

    # 4. 输出
    print(f"{'='*50}")
    print(f"回答")
    print(f"{'='*50}")
    print(response)
    print()

    # 来源
    if hasattr(response, "source_nodes") and response.source_nodes:
        print(f"{'='*50}")
        print(f"参考来源")
        print(f"{'='*50}")
        for i, node in enumerate(response.source_nodes):
            score = node.score if hasattr(node, "score") else "N/A"
            print(f"\n[来源 {i+1}] (相似度: {score:.4f})" if isinstance(score, float)
                  else f"\n[来源 {i+1}]")
            print("-" * 40)
            print(node.text.strip()[:300])
            if len(node.text) > 300:
                print("...")
    print()


if __name__ == "__main__":
    main()

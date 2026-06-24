"""
parse_index.py — RAG Part 1: 解析 + 索引
=========================================
流程：文档 -> 提取文本 -> 分块 -> Embedding -> 存入 ChromaDB

用法：
    python parse_index.py <文件路径>
    python parse_index.py sample.txt
"""

import os
import sys
import json
import requests

# -- 配置 ---------------------------------------------------
OLLAMA_URL = "http://127.0.0.1:11434"
EMBED_MODEL = "qwen3-embedding:4b"      # 专用 Embedding 模型
CHUNK_SIZE = 500                         # 每块字符数
CHUNK_OVERLAP = 50                       # 块间重叠字符数
DB_PATH = os.path.join(os.path.dirname(__file__), "rag_demo_db")
# ----------------------------------------------------------


# -- 1. 文档解析 --------------------------------------------

def extract_text(file_path: str) -> str:
    """根据扩展名读取文档，返回纯文本"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == ".md":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif ext == ".pdf":
        try:
            import pypdf
        except ImportError:
            print("解析 PDF 需要 pypdf 库：pip install pypdf")
            sys.exit(1)
        reader = pypdf.PdfReader(file_path)
        texts = [page.extract_text() for page in reader.pages if page.extract_text()]
        return "\n".join(texts)

    else:
        raise ValueError(f"不支持的文件格式: {ext}（支持 .txt、.md、.pdf）")


# -- 2. 文本分块 --------------------------------------------

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """将文本切分为固定大小的块，保留词边界"""
    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        if end >= text_len:
            chunks.append(text[start:])
            break

        # 在 end 附近向前找词边界（换行符 > 空格 > 直接切）
        boundary = -1
        for pos in range(end, start, -1):
            ch = text[pos]
            if ch == "\n":
                boundary = pos + 1
                break
            elif ch == " " or ch == "\t":
                boundary = pos + 1

        if boundary > start:
            end = boundary
        chunks.append(text[start:end])
        start = end - overlap

    return chunks


# -- 3. Embedding -------------------------------------------

def embed_texts(texts: list[str]) -> list[list[float]]:
    """调用 Ollama Embedding API，返回向量列表"""
    url = f"{OLLAMA_URL}/api/embed"
    payload = {
        "model": EMBED_MODEL,
        "input": texts,
    }
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()

    # /api/embed 返回格式: {"model":..., "embeddings": [[...], ...]}
    return data.get("embeddings", [])


# -- 4. ChromaDB 存储 ---------------------------------------

def store_in_chromadb(chunks: list[str], vectors: list[list[float]]):
    """将文本块和向量存入 ChromaDB"""
    import chromadb

    os.makedirs(DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=DB_PATH)

    # 删除旧集合，确保每次索引都是全新的
    try:
        client.delete_collection("rag_demo")
    except Exception:
        pass

    collection = client.create_collection(
        name="rag_demo",
        metadata={"hnsw:space": "cosine"},
    )

    ids = [f"chunk_{i:05d}" for i in range(len(chunks))]
    collection.add(
        embeddings=vectors,
        documents=chunks,
        ids=ids,
    )

    return len(chunks)


# -- 主流程 ------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("用法: python parse_index.py <文件路径>")
        print("示例: python parse_index.py sample.txt")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"[ERROR] 文件不存在: {file_path}")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"RAG 索引流程 -- Part 1: 解析 + 索引")
    print(f"{'='*50}\n")

    # Step 1: 读取文档
    print(f"[1/4] 读取文档: {os.path.basename(file_path)}")
    text = extract_text(file_path)
    print(f"      [OK] 提取到 {len(text):,} 个字符\n")

    # Step 2: 分块
    print(f"[2/4] 文本分块 (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    chunks = chunk_text(text)
    print(f"      [OK] 生成 {len(chunks)} 个文本块\n")

    # Step 3: Embedding
    print(f"[3/4] 向量化 (模型: {EMBED_MODEL})")
    print(f"      正在调用 Ollama Embedding API...")
    vectors = embed_texts(chunks)

    if not vectors:
        print("[ERROR] Embedding 返回空结果")
        sys.exit(1)

    vec_dim = len(vectors[0])
    print(f"      [OK] 向量维度: {vec_dim}")
    print(f"      [OK] 共 {len(vectors)} 个向量\n")

    # Step 4: 存入 ChromaDB
    print(f"[4/4] 存入 ChromaDB (路径: {DB_PATH})")
    count = store_in_chromadb(chunks, vectors)
    print(f"      [OK] 成功索引 {count} 个文本块\n")

    print(f"{'='*50}")
    print(f"索引完成！共 {count} 个块，向量维度 {vec_dim}")
    print(f"数据库路径: {DB_PATH}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()

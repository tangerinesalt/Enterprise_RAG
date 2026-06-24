"""
parse_index.py — 使用 LlamaIndex 实现：解析 + 索引
=====================================================
流程：文档目录/文件 -> SimpleDirectoryReader -> ChromaDB

对比 01/ 的纯手写版，llama_index 自动处理了：
  - 文档格式检测（PDF/TXT/MD/DOCX 等）
  - 文本分块（内置多种策略）
  - Embedding 调用
  - 向量存储

用法：
    python parse_index.py <文档路径>
    python parse_index.py <目录路径>
"""

import os
import sys

import chromadb
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    Settings,
)
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.readers.file import PDFReader


# -- 配置 ---------------------------------------------------
OLLAMA_URL = "http://127.0.0.1:11434"
EMBED_MODEL = "qwen3-embedding:4b"
DB_PATH = os.path.join(os.path.dirname(__file__), "rag_demo_db_llama")

# OCR 兜底：当 PDF 提取不到文字时，尝试用 OCR
# 需要安装：pip install rapidocr-onnxruntime pypdfium2
# 设为 False 则跳过 OCR，直接报错
ENABLE_OCR_FALLBACK = True
# ----------------------------------------------------------


# -- PDF 鲁棒读取（pypdf + OCR 兜底）------------------------

def _ocr_pdf(file_path: str) -> str:
    """
    OCR 识别图片型 PDF（扫描件）。
    将 PDF 每页渲染为图像，然后用 rapidocr 识别文字。
    """
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        print("      [警告] 未安装 rapidocr-onnxruntime，跳过 OCR")
        print("      安装: pip install rapidocr-onnxruntime")
        return ""

    try:
        import pypdfium2 as pdfium
    except ImportError:
        print("      [警告] 未安装 pypdfium2，跳过 OCR")
        print("      安装: pip install pypdfium2")
        return ""

    try:
        ocr = RapidOCR()
        all_lines = []

        pdf = pdfium.PdfDocument(file_path)
        for i in range(len(pdf)):
            page = pdf[i]
            # 2x 缩放提高小字识别率
            bitmap = page.render(scale=2.0)
            img = bitmap.to_numpy()
            result, _ = ocr(img)
            if result:
                for item in result:
                    if item[1]:  # item = [box, text, score]
                        all_lines.append(item[1])
            page.close()

        pdf.close()
        return "\n".join(all_lines)

    except Exception as e:
        print(f"      [警告] OCR 过程出错: {e}")
        return ""



class RobustPDFReader(PDFReader):
    """
    自定义 PDFReader：支持 OCR 兜底。
    按页返回 Document 列表（与原始 PDFReader 行为一致）。
    """

    def load_data(self, *args, **kwargs):
        file_path = kwargs.get("file_path", args[0] if args else None)
        if not (file_path and os.path.exists(file_path)):
            return super().load_data(*args, **kwargs)

        # 先用 pypdf 尝试逐页提取
        import pypdf
        reader = pypdf.PdfReader(file_path)

        documents = []
        for page_num, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            documents.append((text, page_num))

        # 判断是否大部分页面为空 -> 需要 OCR
        total = len(documents)
        empty = sum(1 for t, _ in documents if not t)
        text_len = sum(len(t) for t, _ in documents)

        if (text_len < 50 or empty / max(total, 1) > 0.5) and ENABLE_OCR_FALLBACK:
            print(f"      [提示] pypdf 仅提取到 {text_len} 字符"
                  f"（{empty}/{total} 页为空），切换到 OCR...")
            ocr_text = _ocr_pdf(file_path)
            if ocr_text.strip():
                print(f"      [OK] OCR 提取到 {len(ocr_text):,} 个字符")
                # OCR 结果是连续的，不分页
                from llama_index.core import Document
                return [Document(
                    text=ocr_text,
                    metadata={"file_path": file_path, "page_label": "ocr"},
                )]

        # pypdf 成功，按页返回
        from llama_index.core import Document
        return [
            Document(
                text=text,
                metadata={
                    "file_path": file_path,
                    "page_label": f"p{page_num + 1}",
                },
            )
            for text, page_num in documents
            if text.strip()
        ]


# -- 主流程 ------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("用法: python parse_index.py <文件或目录路径>")
        print("示例: python parse_index.py sample.txt")
        print("示例: python parse_index.py ./docs/")
        sys.exit(1)

    input_path = sys.argv[1]

    if not os.path.exists(input_path):
        print(f"[ERROR] 路径不存在: {input_path}")
        sys.exit(1)

    print(f"\n{'='*50}")
    print(f"LlamaIndex -- Part 1: 解析 + 索引")
    print(f"{'='*50}\n")

    # 1. 配置全局 Embedding 模型
    print(f"[配置] Embedding 模型: {EMBED_MODEL}")
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=OLLAMA_URL,
    )

    # 2. 读取文档
    #    不论单文件还是目录，PDF 都用 RobustPDFReader（含 OCR 兜底）
    print(f"[1/3] 读取文档: {input_path}")

    pdf_extractor = {".pdf": RobustPDFReader()}

    if os.path.isfile(input_path):
        file_dir = os.path.dirname(input_path) or "."
        reader = SimpleDirectoryReader(
            input_dir=file_dir,
            input_files=[input_path],
            file_extractor=pdf_extractor,
        )
    else:
        reader = SimpleDirectoryReader(
            input_dir=input_path,
            recursive=True,
            file_extractor=pdf_extractor,
        )

    documents = reader.load_data()
    node_parser = SimpleNodeParser.from_defaults(chunk_size=500)
    # split into nodes
    base_nodes = node_parser.get_nodes_from_documents(documents=documents)
    print(f"      [OK] 加载了 {len(documents)} 个文档块\n")

    if not documents:
        print("[ERROR] 未能从路径中读取到任何文档")
        sys.exit(1)

    # 3. 初始化 ChromaDB 持久化
    print(f"[2/3] 初始化 ChromaDB (路径: {DB_PATH})")
    os.makedirs(DB_PATH, exist_ok=True)
    db = chromadb.PersistentClient(path=DB_PATH)

    try:
        db.delete_collection("rag_demo")
    except Exception:
        pass

    chroma_collection = db.create_collection("rag_demo")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    print(f"      [OK] ChromaDB 集合已创建\n")

    # 4. 构建索引（自动完成：分块 -> Embedding -> 存储）
    print(f"[3/3] 构建向量索引...")
    print(f"      正在调用 Ollama Embedding API（按文档块数等待）...")
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )
    print(f"      [OK] 索引构建完成！\n")

    # 打印摘要信息
    print(f"{'='*50}")
    print(f"索引完成！")
    print(f"文档: {input_path}")
    print(f"向量数: {chroma_collection.count()}")
    print(f"数据库: {DB_PATH}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()

"""
Indexer — 基于 llama_index 的文档解析、分块、Embedding、索引。

复用 example/02/ 中的 RobustPDFReader + OllamaEmbedding。
"""

import os
import sys

import chromadb
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    Settings,
    Document,
)
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.readers.file import PDFReader

from config.settings import ENABLE_OCR_FALLBACK
from config.init import init_models
from app.modules.kb_manager import KnowledgeBase
from app.modules.kb_manager.chunker import chunk_documents


# ── 全局初始化（一次配好 Embedding + LLM）──
init_models()

_kb = KnowledgeBase()


# ── OCR 兜底 ─────────────────────────────────────

def _ocr_pdf(file_path: str) -> str:
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return ""
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return ""

    try:
        ocr = RapidOCR()
        all_lines = []
        pdf = pdfium.PdfDocument(file_path)
        for i in range(len(pdf)):
            page = pdf[i]
            bitmap = page.render(scale=2.0)
            img = bitmap.to_numpy()
            result, _ = ocr(img)
            if result:
                for item in result:
                    if item[1]:
                        all_lines.append(item[1])
            page.close()
        pdf.close()
        return "\n".join(all_lines)
    except Exception:
        return ""


# ── RobustPDFReader ──────────────────────────────

class RobustPDFReader(PDFReader):
    """支持 OCR 兜底的 PDF 读取器。按页返回 Document。"""

    def load_data(self, *args, **kwargs):
        file_path = kwargs.get("file_path", args[0] if args else None)
        if not (file_path and os.path.exists(file_path)):
            return super().load_data(*args, **kwargs)

        import pypdf
        reader = pypdf.PdfReader(file_path)

        docs = []
        for page_num, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            docs.append((text, page_num))

        total = len(docs)
        empty = sum(1 for t, _ in docs if not t)
        text_len = sum(len(t) for t, _ in docs)

        if (text_len < 50 or empty / max(total, 1) > 0.5) and ENABLE_OCR_FALLBACK:
            ocr_text = _ocr_pdf(file_path)
            if ocr_text.strip():
                return [Document(
                    text=ocr_text,
                    metadata={"file_path": file_path, "page_label": "ocr"},
                )]

        return [
            Document(
                text=text,
                metadata={"file_path": file_path, "page_label": f"p{page_num + 1}"},
            )
            for text, page_num in docs
            if text.strip()
        ]


# ── Indexer ──────────────────────────────────────

class Indexer:
    """文档索引器。每个知识库对应独立的 ChromaDB 实例。"""

    def __init__(self):
        self._pdf_extractor = {".pdf": RobustPDFReader()}

    def _get_chroma_collection(self, kb_name: str):
        """获取知识库对应的 ChromaDB collection"""
        _kb.ensure_exists(kb_name)
        db_path = _kb.vector_db_path(kb_name)
        os.makedirs(db_path, exist_ok=True)
        db = chromadb.PersistentClient(path=db_path)
        collection = db.get_or_create_collection(
            name="kb_index",
            metadata={"hnsw:space": "cosine"},
        )
        return db, collection

    # ── 索引单个文件 ────────────────────────

    def index_file(self, kb_name: str, filename: str) -> int:
        """
        对知识库中的指定文件执行索引（解析 → 分块 → Embedding → 存储）。

        返回索引的块数。
        """
        _kb.ensure_exists(kb_name)
        file_path = _kb.file_path(kb_name, filename)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"知识库内文件不存在: {file_path}")

        # 先清理同名文件的旧向量，保证幂等
        self.delete_vectors(kb_name, filename)

        db, collection = self._get_chroma_collection(kb_name)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # 用 SimpleDirectoryReader 读取单个文件
        file_dir = os.path.dirname(file_path) or "."
        reader = SimpleDirectoryReader(
            input_dir=file_dir,
            input_files=[file_path],
            file_extractor=self._pdf_extractor,
        )
        documents = reader.load_data()

        if not documents:
            return 0

        # 自定义组合分块：页面类型检测 → SentenceSplitter → metadata 注入
        nodes = chunk_documents(documents)

        # 从 nodes 构建索引
        index = VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
        )

        return collection.count()

    # ── 按文件名删除向量 ─────────────────────

    def delete_vectors(self, kb_name: str, filename: str) -> int:
        """
        删除 ChromaDB 中所有属于指定文件的向量。
        通过 metadata 中的 file_path 字段匹配文件绝对路径。

        返回删除的向量数。
        """
        _kb.ensure_exists(kb_name)
        db, collection = self._get_chroma_collection(kb_name)

        abs_path = _kb.file_path(kb_name, filename)

        # ChromaDB 的 where 过滤
        result = collection.get(where={"file_path": abs_path})
        ids = result.get("ids", [])

        if ids:
            collection.delete(ids=ids)

        return len(ids)

    # ── 重新索引 ────────────────────────────

    def reindex_file(self, kb_name: str, filename: str) -> int:
        """删除旧向量 → 重新索引。返回索引的块数。"""
        self.delete_vectors(kb_name, filename)
        return self.index_file(kb_name, filename)

    # ── 批量索引 ────────────────────────────

    def index_folder(self, kb_name: str, folder_name: str) -> dict:
        """
        递归索引文件夹中的所有文件。
        返回 {filename: chunk_count} 映射。
        """
        _kb.ensure_exists(kb_name)
        files = _kb.list_folder_files(kb_name, folder_name)

        if not files:
            raise FileNotFoundError(
                f"文件夹 '{folder_name}' 中没有可索引的文件"
            )

        results = {}
        for rel_path in files:
            try:
                count = self.index_file(kb_name, rel_path)
                results[rel_path] = count
            except Exception as e:
                results[rel_path] = f"ERROR: {e}"

        return results

    def index_all(self, kb_name: str) -> dict:
        """
        索引知识库 files/ 中所有文件（递归遍历所有子目录）。
        返回 {filename: chunk_count} 映射。
        """
        _kb.ensure_exists(kb_name)
        fdir = _kb.files_path(kb_name)
        if not os.path.isdir(fdir):
            return {}

        # 收集所有文件（递归）
        all_files = []
        for root, _, files in os.walk(fdir):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), fdir)
                all_files.append(rel.replace("\\", "/"))

        results = {}
        for rel_path in sorted(all_files):
            try:
                count = self.index_file(kb_name, rel_path)
                results[rel_path] = count
            except Exception as e:
                results[rel_path] = f"ERROR: {e}"

        return results

"""
Indexer — 基于 llama_index 的文档解析、分块、Embedding、索引。

复用 example/02/ 中的 RobustPDFReader + OllamaEmbedding。
"""

import os
import sys
import logging

import chromadb
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    StorageContext,
    Settings,
    Document,
)
from llama_index.core.schema import MetadataMode
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.readers.file import PDFReader

from config.settings import ENABLE_OCR_FALLBACK
from config.init import init_models
from app.modules.kb_manager import KnowledgeBase
from app.modules.kb_manager.chunker import chunk_documents

logger = logging.getLogger(__name__)


# ── 全局初始化（一次配好 Embedding + LLM）──
init_models()

_kb = KnowledgeBase()


# ── OCR 表格识别可用性检测（首次调用自动探测）───
_table_recognition_available = None


def _check_table_recognition() -> bool:
    """检测 rapid-table 是否可用，结果缓存避免重复 import。"""
    global _table_recognition_available
    if _table_recognition_available is None:
        try:
            from rapid_table import RapidTable
            RapidTable()
            _table_recognition_available = True
            logger.info("table recognition enabled (rapid-table available)")
        except ImportError:
            _table_recognition_available = False
            logger.info("table recognition disabled (rapid-table not installed)")
        except Exception as e:
            _table_recognition_available = False
            logger.warning("table recognition disabled: %s", e)
    return _table_recognition_available


# ── OCR 兜底 ─────────────────────────────────────

def _ocr_pdf(file_path: str) -> list[str]:
    """OCR 逐页识别 PDF，返回每页文本列表。

    首次调用时自动检测 rapid-table 是否可用。
    如果可用则启用表格结构识别（RapidTable SLANet），
    否则使用 RapidOCR 纯文本识别。

    返回 list[str]，每个元素为一页的识别结果（空页返回空字符串）。
    """
    if _check_table_recognition():
        try:
            return _ocr_pdf_with_tables(file_path)
        except Exception:
            logger.warning("table recognition failed, falling back to plain OCR", exc_info=True)

    return _ocr_pdf_plain(file_path)


def _ocr_pdf_plain(file_path: str) -> list[str]:
    """RapidOCR 纯文本识别。"""
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        return []
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return []

    try:
        ocr = RapidOCR()
        pdf = pdfium.PdfDocument(file_path)
        page_texts = []

        for i in range(len(pdf)):
            page = pdf[i]
            bitmap = page.render(scale=2.0)
            img = bitmap.to_numpy()
            result, _ = ocr(img)
            page_lines = []
            if result:
                for item in result:
                    if item[1]:
                        page_lines.append(item[1])
            page_texts.append("\n".join(page_lines))
            page.close()

        pdf.close()
        return page_texts
    except Exception:
        return []


# ── 扫描件表格识别（RapidTable）────────────────

def _html_table_to_markdown(html: str) -> str:
    """将 HTML table 转为 Markdown 格式。

    处理 colspan 合并单元格（用重复空列填充），
    不支持 rowspan（超出部分丢弃）。
    """
    if "<table" not in html:
        return html.strip()

    import re
    rows = []
    # 提取所有 <tr> 内容
    tr_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
    td_pattern = re.compile(r"<t[hd][^>]*>(.*?)</t[hd]>", re.DOTALL | re.IGNORECASE)
    colspan_pattern = re.compile(r"colspan\s*=\s*['\"]?(\d+)['\"]?", re.IGNORECASE)

    for tr_match in tr_pattern.finditer(html):
        tr_content = tr_match.group(1)
        cells = []
        for td_match in td_pattern.finditer(tr_content):
            td_html = td_match.group(0)
            cell_text = re.sub(r"<[^>]+>", "", td_match.group(1)).strip()
            # 检查 colspan
            colspan = 1
            cs = colspan_pattern.search(td_html)
            if cs:
                colspan = int(cs.group(1))
            cells.extend([cell_text] + [""] * (colspan - 1))
        if cells:
            rows.append(cells)

    if not rows:
        return html.strip()

    col_count = max(len(r) for r in rows)

    def fmt(cells):
        padded = cells + [""] * (col_count - len(cells))
        return "| " + " | ".join(padded) + " |"

    lines = [fmt(rows[0])]
    lines.append("|" + "|".join("---" for _ in range(col_count)) + "|")
    for row in rows[1:]:
        lines.append(fmt(row))

    return "\n".join(lines)


def _ocr_pdf_with_tables(file_path: str) -> list[str]:
    """RapidTable 表格识别(含单元格OCR)，无表页回退 RapidOCR。"""
    try:
        from rapid_table import RapidTable
    except ImportError:
        logger.warning("rapid-table not installed, falling back to plain OCR")
        return _ocr_pdf_plain(file_path)

    try:
        import pypdfium2 as pdfium
    except ImportError:
        return _ocr_pdf_plain(file_path)

    try:
        engine = RapidTable()
        pdf = pdfium.PdfDocument(file_path)
        page_texts = []

        for i in range(len(pdf)):
            page = pdf[i]
            bitmap = page.render(scale=2.0)
            img = bitmap.to_numpy()
            page.close()

            # 尝试 RapidTable 表格识别
            try:
                from PIL import Image
                import io
                buf = io.BytesIO()
                Image.fromarray(img).save(buf, format="PNG")
                buf.seek(0)
                result = engine(buf.read())
            except Exception:
                result = None

            if result and hasattr(result, "pred_htmls") and result.pred_htmls:
                # 有表格 → 转为 Markdown
                html = result.pred_htmls[0]
                md = _html_table_to_markdown(html)
                page_texts.append(md)
            else:
                # 无表格 → RapidOCR 纯文本
                from rapidocr_onnxruntime import RapidOCR
                ocr = RapidOCR()
                ocr_result, _ = ocr(img)
                lines = []
                if ocr_result:
                    for item in ocr_result:
                        if item[1]:
                            lines.append(item[1])
                page_texts.append("\n".join(lines))

        pdf.close()
        return page_texts
    except Exception:
        logger.warning("RapidTable failed for %s, falling back", file_path, exc_info=True)
        return _ocr_pdf_plain(file_path)


# ── PDF 表格抽取（pdfplumber）───────────────────

def _table_to_markdown(table: list[list[str]]) -> str:
    """将 pdfplumber 的表格数据转为 Markdown 格式。

    输出示例：
        | 版本 | 修订日期 | 修订内容 | 修订人 |
        |------|---------|---------|--------|
        | B/0 | 2023.6.1 | 全文改版新订 | 人力资源部 |
    """
    if not table or not table[0]:
        return ""

    rows = []
    for row in table:
        # 跳过完全空行
        cleaned = [c.strip() if c else "" for c in row]
        if all(not c for c in cleaned):
            continue
        rows.append(cleaned)

    if not rows:
        return ""

    # 计算每列最大宽度用于对齐（不限死长度，保证可读即可）
    col_count = max(len(r) for r in rows)

    def format_row(cells):
        padded = cells + [""] * (col_count - len(cells))
        return "| " + " | ".join(padded[:col_count]) + " |"

    lines = [format_row(rows[0])]
    # 分隔行
    lines.append("|" + "|".join("---" for _ in range(col_count)) + "|")
    for row in rows[1:]:
        lines.append(format_row(row))

    return "\n".join(lines)


def _extract_tables_pdfplumber(file_path: str) -> dict[int, list[str]]:
    """用 pdfplumber 提取 PDF 中的表格，返回 {页码0: [Markdown表格, ...]}。

    对无表格或扫描件返回空 dict，不阻塞后续处理。
    """
    try:
        import pdfplumber as _plumber
    except ImportError:
        logger.warning("pdfplumber not installed, skipping table extraction")
        return {}

    try:
        result: dict[int, list[str]] = {}
        with _plumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                if not tables:
                    continue
                md_tables = []
                for t in tables:
                    md = _table_to_markdown(t)
                    if md:
                        md_tables.append(md)
                if md_tables:
                    result[page_num] = md_tables
        return result
    except Exception as e:
        logger.warning("pdfplumber table extraction failed for %s: %s", file_path, e)
        return {}


# ── RobustPDFReader ──────────────────────────────

class RobustPDFReader(PDFReader):
    """支持 OCR 兜底 + pdfplumber 表格抽取的 PDF 读取器。按页返回 Document。"""

    def load_data(self, *args, **kwargs):
        file_path = kwargs.get("file_path", args[0] if args else None)
        if not (file_path and os.path.exists(file_path)):
            return super().load_data(*args, **kwargs)

        # ① pdfplumber 抽取表格（非扫描件有表格数据，扫描件返回空）
        tables = _extract_tables_pdfplumber(file_path)

        import pypdf
        reader = pypdf.PdfReader(file_path)

        docs = []
        for page_num, page in enumerate(reader.pages):
            text = (page.extract_text() or "").strip()
            # ② 合并该页的表格 Markdown 到文本中
            page_tables = tables.get(page_num, [])
            if page_tables:
                text += "\n\n" + "\n\n".join(page_tables)
            docs.append((text, page_num))

        total = len(docs)
        empty = sum(1 for t, _ in docs if not t)
        text_len = sum(len(t) for t, _ in docs)

        if (text_len < 50 or empty / max(total, 1) > 0.5) and ENABLE_OCR_FALLBACK:
            page_texts = _ocr_pdf(file_path)
            if page_texts:
                return [
                    Document(
                        text=pt,
                        metadata={"file_path": file_path, "page_label": f"ocr_p{i+1}"},
                    )
                    for i, pt in enumerate(page_texts)
                ]

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
        chunk_count = len(nodes)

        # 从 nodes 构建索引
        index = VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
        )

        _kb.set_file_status(kb_name, filename, "indexed", chunks=chunk_count)
        return chunk_count

    # ── 流式索引（逐 chunk 报告进度）───────────

    def index_file_stream(self, kb_name: str, filename: str):
        """
        Generator: 对指定文件执行索引，逐 chunk 产出 SSE 进度事件。

        事件类型:
            index_start:   {"type": "index_start",   "file": str, "total_chunks": int}
            index_progress:{"type": "index_progress", "file": str, "current": int, "total": int, "pct": int}
            index_done:    {"type": "index_done",     "file": str, "chunks": int}
        """
        _kb.ensure_exists(kb_name)
        file_path = _kb.file_path(kb_name, filename)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"知识库内文件不存在: {file_path}")

        # 先清理同名文件的旧向量
        self.delete_vectors(kb_name, filename)

        db, collection = self._get_chroma_collection(kb_name)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # 读取文件
        file_dir = os.path.dirname(file_path) or "."
        reader = SimpleDirectoryReader(
            input_dir=file_dir,
            input_files=[file_path],
            file_extractor=self._pdf_extractor,
        )
        documents = reader.load_data()

        if not documents:
            yield {"type": "index_start", "file": filename, "total_chunks": 0}
            yield {"type": "index_done", "file": filename, "chunks": 0}
            return

        # 分块
        nodes = chunk_documents(documents)
        total = len(nodes)

        yield {"type": "index_start", "file": filename, "total_chunks": total}

        # 预计算 embedding，逐 chunk 报告进度
        embed_model = Settings.embed_model
        for i, node in enumerate(nodes):
            if node.embedding is None:
                text = node.get_content(metadata_mode=MetadataMode.EMBED)
                node.embedding = embed_model.get_text_embedding(text)
            pct = round((i + 1) / total * 100)
            yield {"type": "index_progress", "file": filename, "current": i + 1, "total": total, "pct": pct}

        # 构建索引（VectorStoreIndex 复用预计算 embedding，跳过重算）
        VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
        )

        chunk_count = total
        _kb.set_file_status(kb_name, filename, "indexed", chunks=chunk_count)
        yield {"type": "index_done", "file": filename, "chunks": chunk_count}

    def index_folder_stream(self, kb_name: str, folder_name: str):
        """
        Generator: 递归索引文件夹中所有文件，所有文件的事件合并到一个流。
        """
        _kb.ensure_exists(kb_name)
        files = _kb.list_folder_files(kb_name, folder_name)

        if not files:
            raise FileNotFoundError(f"文件夹 '{folder_name}' 中没有可索引的文件")

        for rel_path in files:
            try:
                yield from self.index_file_stream(kb_name, rel_path)
            except Exception as e:
                yield {"type": "index_error", "file": rel_path, "message": str(e)}

    def index_all_stream(self, kb_name: str):
        """
        Generator: 索引知识库 files/ 中所有文件，所有文件的事件合并到一个流。
        跳过已经索引的文件。
        """
        _kb.ensure_exists(kb_name)
        fdir = _kb.files_path(kb_name)
        if not os.path.isdir(fdir):
            return

        # 加载索引状态，用于跳过已索引文件
        index_status = _kb._load_index_status(kb_name)
        file_count = 0
        for root, _, files in os.walk(fdir):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), fdir)
                rel = rel.replace("\\", "/")
                # 跳过已索引文件
                if index_status.get("files", {}).get(rel, {}).get("status") == "indexed":
                    continue
                try:
                    yield from self.index_file_stream(kb_name, rel)
                    file_count += 1
                except Exception as e:
                    yield {"type": "index_error", "file": rel, "message": str(e)}

        yield {"type": "index_done", "status": "all_complete", "files": file_count}

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
        跳过已经索引的文件。返回 {filename: chunk_count} 映射。
        """
        _kb.ensure_exists(kb_name)
        fdir = _kb.files_path(kb_name)
        if not os.path.isdir(fdir):
            return {}

        # 加载索引状态，用于跳过已索引文件
        index_status = _kb._load_index_status(kb_name)

        results = {}
        for root, _, files in os.walk(fdir):
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), fdir)
                rel = rel.replace("\\", "/")
                # 跳过已索引文件
                if index_status.get("files", {}).get(rel, {}).get("status") == "indexed":
                    continue
                try:
                    count = self.index_file(kb_name, rel)
                    results[rel] = count
                except Exception as e:
                    results[rel] = f"ERROR: {e}"

        return results

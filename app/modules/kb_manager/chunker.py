"""
Chunker — 文档分块策略：SentenceSplitter 自定义参数 + metadata 继承。

支持跨页重复文本剥离（页眉页脚去重），在分块前自动检测并清理。

用法：
    from app.modules.kb_manager.chunker import chunk_documents
    nodes = chunk_documents(documents)
"""

from collections import Counter

from llama_index.core.node_parser import SentenceSplitter
from config.settings import CHUNK_SIZE, CHUNK_OVERLAP, CHUNK_PARAGRAPH_SEPARATOR
from app.utils.logging import get_logger

logger = get_logger(__name__)


def strip_page_repeats(
    documents: list,
    head_lines: int = 5,
    tail_lines: int = 3,
    threshold: float = 0.5,
) -> list:
    """检测并移除跨页重复文本（页眉页脚）。

    原理：
        对同一文件的所有页面，收集每页前 head_lines 行、后 tail_lines 行，
        统计各行的跨页出现率。出现率 >= threshold 的行视为页眉或页脚，
        从所有页面中剥离。

    参数：
        documents: Document 列表，每个 Document 代表一页
        head_lines: 从每页开头检测的行数（默认 5）
        tail_lines: 从每页末尾检测的行数（默认 3）
        threshold: 判定为重复的页数比例阈值（默认 0.5）

    返回：
        清洗后的 Document 列表（顺序不变）
    """
    # 按 file_path 分组
    from collections import defaultdict
    groups = defaultdict(list)
    for doc in documents:
        fp = doc.metadata.get("file_path", "")
        groups[fp].append(doc)

    # 用于跟踪哪些文件被清理了
    cleaned = 0
    for fp, pages in groups.items():
        if len(pages) < 3:
            continue  # 短文档不检测

        # 收集每页的边界行
        all_head_lines = []
        all_tail_lines = []
        for p in pages:
            lines = p.text.split("\n")
            all_head_lines.extend(lines[:head_lines])
            all_tail_lines.extend(lines[-tail_lines:] if len(lines) >= tail_lines else lines)

        # 统计每行出现的页数
        head_counter = Counter(all_head_lines)
        tail_counter = Counter(all_tail_lines)
        total = len(pages)
        min_count = int(total * threshold) + 1

        # 构建要去除的 set（忽略空白行，避免破坏段落结构）
        to_strip = set()
        for line, count in head_counter.items():
            if count >= min_count and line.strip():
                to_strip.add(line)
        for line, count in tail_counter.items():
            if count >= min_count and line.strip():
                to_strip.add(line)

        if not to_strip:
            continue  # 没有重复文本

        # 从每页剥离
        for p in pages:
            page_lines = p.text.split("\n")
            cleaned_lines = [l for l in page_lines if l not in to_strip]
            p.set_content("\n".join(cleaned_lines))

        cleaned += 1
        logger.debug(
            "header_dedup | %s stripped %d lines from %d pages",
            fp, len(to_strip), total,
        )

    if cleaned:
        logger.info("header_dedup | cleaned %d/%d files", cleaned, len(groups))
    return documents


def _fix_orphan_table_fragments(all_nodes: list) -> list:
    """后处理：为丢失列头的表格碎片 node 补全表头。

    SentenceSplitter 不感知 Markdown 表格边界，切分后部分 node 含有
    表格数据（`| ... |`）但丢失了列头分离线（`---|---|`）。
    此函数从最近的完整表头 node 继承列头，补到碎片 node 前面。
    """
    current_header = None  # 列头行，如 "| 名称 | 审批人 |"
    current_sep = None     # 分离线，如 "|-----|-------|"
    fixed_count = 0
    total_nodes = len(all_nodes)

    import re
    sep_pattern = re.compile(r"^\|[-|\s]+\|$", re.MULTILINE)

    for node in all_nodes:
        text = node.text
        # 检查是否包含表格分离线（|---|）
        has_separator = bool(sep_pattern.search(text))

        if has_separator:
            # 此 node 包含完整表头 → 缓存列头和分离线
            lines = text.split("\n")
            for j, line in enumerate(lines):
                if sep_pattern.match(line.strip()):
                    if j > 0:
                        current_header = lines[j - 1].strip()
                    current_sep = line.strip()
                    break

        elif "|" in text and current_header and current_sep:
            # 有管道符但没有分离线 → orphan 碎片 → 补表头
            node.text = current_header + "\n" + current_sep + "\n" + node.text
            fixed_count += 1

    if fixed_count:
        logger.info(
            "table_fix | fixed %d orphan table fragments across %d nodes",
            fixed_count, total_nodes,
        )
    return all_nodes


def chunk_documents(documents: list) -> list:
    """自定义分块：strip_page_repeats → SentenceSplitter → table_fix → metadata。"""
    # 跨页重复文本剥离（页眉页脚去重）
    documents = strip_page_repeats(documents)

    parser = SentenceSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        paragraph_separator=CHUNK_PARAGRAPH_SEPARATOR,
    )

    all_nodes = []
    for doc in documents:
        # 去除 UTF-8 BOM 字符
        doc.set_content(doc.text.lstrip("﻿"))
        nodes = parser.get_nodes_from_documents([doc])
        for i, node in enumerate(nodes):
            node.text = node.text.lstrip("﻿")
            node.metadata["chunk_index"] = i
            node.metadata["total_chunks"] = len(nodes)
            for key in ("file_path", "page_label"):
                if key in doc.metadata and key not in node.metadata:
                    node.metadata[key] = doc.metadata[key]

        all_nodes.extend(nodes)

    # 后处理：修复被切碎的表格 column header
    all_nodes = _fix_orphan_table_fragments(all_nodes)

    return all_nodes

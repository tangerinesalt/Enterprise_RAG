"""
Chunker — 文档分块策略：SentenceSplitter 自定义参数 + metadata 继承。

用法：
    from app.modules.kb_manager.chunker import chunk_documents
    nodes = chunk_documents(documents)
"""

from llama_index.core.node_parser import SentenceSplitter
from config.settings import CHUNK_SIZE, CHUNK_OVERLAP, CHUNK_PARAGRAPH_SEPARATOR


def chunk_documents(documents: list) -> list:
    """自定义分块：SentenceSplitter(512/128) → metadata 继承。"""
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

    return all_nodes

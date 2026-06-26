## Context

当前 `indexer.py` 的索引流程：
```
SimpleDirectoryReader.load_data() → List[Document]
    ↓
VectorStoreIndex.from_documents(documents)
    ↓ (内部)
Settings.node_parser = SentenceSplitter(chunk_size=1024, overlap=200)
    ↓
List[TextNode] → ChromaDB
```

关键问题：
- 1024 token 的块对中文标准文档过大，一个块包含多个主题
- 无页面类型标记，封面/目录/正文混在一起
- 块大小不可控（31~4962 字符），小碎片和大目录影响检索质量

## Goals / Non-Goals

**Goals:**
- 自定义组合 NodeParser，使用 `from_nodes()` 完全控制分块
- 块大小稳定在 ~512 tokens，overlap 128 tokens
- 为每个节点标注 `page_type`（cover/toc/foreword/content/ocr_scanned）
- 分块参数配置化（settings.py）
- 兼容现有 ChromaDB 结构，只需 reindex 无需改 schema

**Non-Goals:**
- 不换 PDF 解析器（RobustPDFReader 继续用）
- 不改检索器逻辑（`build_retriever` 的 MetadataFilters 自动适配新标记）
- 不引入语义分块模型（SemanticSplitterNodeParser 留给后续）

## Strategy — 企业级组合 NodeParser

```
文档 (PDF)
    │
    ▼
RobustPDFReader (逐页读取，保持 page_label metadata)
    │
    ▼
List[Document] (每页一个 Document, metadata.page_label = "p1"/"p2"/...)
    │
    ▼
Custom NodeParser Pipeline
    │
    ├── 1. 页面类型检测 (启发式规则)
    │      p1           → page_type = "cover"
    │      p2-p4        → page_type = "toc"
    │      p5           → page_type = "foreword"
    │      p6+          → page_type = "content"
    │      ocr          → page_type = "ocr_scanned"
    │
    ├── 2. SentenceSplitter 切分
    │      chunk_size=512
    │      chunk_overlap=128
    │      paragraph_separator="\n\n"
    │
    ├── 3. 为每个 TextNode 注入 metadata
    │      │
    │      ├── page_type: "content"
    │      ├── file_path: "kb/光伏信息/files/xxx.pdf"
    │      ├── page_label: "p6"
    │      ├── chunk_index: 2
    │      └── total_chunks: 3
    │
    ▼
List[TextNode] → VectorStoreIndex(nodes=nodes, storage_context=...)
    │
    ▼
ChromaDB (每个 node 一条记录，metadata 完整)
```

## Decisions

### 1. 分块参数选择

| 参数 | 默认值 | 新值 | 理由 |
|------|--------|------|------|
| chunk_size | 1024 | **512** | 中文 512 token ≈ 512~1024 字符，约 1-2 个段落 |
| chunk_overlap | 200 | **128** | 保持上下文连贯但不过度膨胀 |
| paragraph_separator | `\n\n\n` | `\n\n` | PDF 文本提取后段落间距不稳定，双换行更合适 |

### 2. 页面类型启发式检测

基于页面位置和文本特征，而非内容分析（避免额外依赖）：

```python
def _detect_page_type(page_label: str, text: str) -> str:
    """基于页面位置和内容特征检测页面类型。"""
    label = page_label.lower().strip()
    if label == "p1":
        return "cover"        # 第1页：封面/标题页
    elif label in ("p2", "p3", "p4"):
        return "toc"          # 2-4页：通常为目录
    elif label == "p5":
        if "前言" in text[:100] or "foreword" in text[:100].lower():
            return "foreword"  # 第5页：前言
    elif label.startswith("ocr"):
        return "ocr_scanned"  # OCR 兜底页
    
    return "content"          # 其他：正文
```

### 3. 配置文件新增项 (`config/settings.py`)

```python
# 分块策略
CHUNK_SIZE = 512
CHUNK_OVERLAP = 128
CHUNK_PARAGRAPH_SEPARATOR = "\n\n"
```

### 4. `from_nodes` 流程

```python
from llama_index.core.node_parser import SentenceSplitter

# 1. 读取文档（保持 page_label）
documents = reader.load_data()

# 2. 全局 SentenceSplitter 配置
parser = SentenceSplitter(
    chunk_size=Settings.CHUNK_SIZE,
    chunk_overlap=Settings.CHUNK_OVERLAP,
    paragraph_separator=Settings.CHUNK_PARAGRAPH_SEPARATOR,
)

# 3. 逐 Document 处理，注入 metadata
all_nodes = []
for doc in documents:
    page_label = doc.metadata.get("page_label", "")
    page_type = _detect_page_type(page_label, doc.text)
    
    nodes = parser.get_nodes_from_documents([doc])
    for i, node in enumerate(nodes):
        node.metadata["page_type"] = page_type
        node.metadata["page_label"] = page_label
        node.metadata["chunk_index"] = i
        node.metadata["total_chunks"] = len(nodes)

# 4. 从 nodes 构建索引
index = VectorStoreIndex(
    nodes=all_nodes,
    storage_context=storage_context,
    show_progress=True,
)
```

### 5. 检索器适配

`build_retriever` 中的 MetadataFilters 同步更新：

```python
filters = [
    # 页面类型过滤
    ExactMatchFilter(key="page_type", value="cover", operator="!="),
    ExactMatchFilter(key="page_type", value="toc", operator="!="),
    ExactMatchFilter(key="page_type", value="foreword", operator="!="),
    ExactMatchFilter(key="page_type", value="ocr_scanned", operator="!="),
]
```

这比原来的硬编码 page_label 更健壮（不同 PDF 前言可能在 p5 也可能在 p6）。

## Migration

现有 KB 需要手动触发 reindex：
```python
python -m app.cli kb reindex 光伏信息 filename.pdf
```

或通过 API `POST /api/kb/reindex`。

## Risks / Trade-offs

- **[Risk] 页面类型检测不准确**：启发式规则基于位置，不同 PDF 的页面结构可能不同。→ `content` 为默认值，误判只影响过滤粒度，不丢失内容。
- **[Risk] 512 字符分块可能打断关键段落**：部分技术规范段落可能超过 512 字符。→ overlap=128 补偿上下文丢失。
- **[Risk] 重新索引耗时**：需重新解析 PDF + Embedding。→ 与首次索引时间相同，可分批进行。

## Context

当前 `chat_stream()` 和 `chat()` 中的检索逻辑：
```python
query_engine = index.as_query_engine(similarity_top_k=5)
response = query_engine.query(query)
```

这是一个黑盒调用，无法控制过滤条件、分数阈值或检索策略。实际观测到向量检索对所有 108 个块打出几乎相同的分数（0.59~0.60），且封面、前言、目录、起草人名单等无意义页面频繁出现在 Top-5 中。

## Goals / Non-Goals

**Goals:**
- 过滤掉封面页、前言、目录、起草人名单等无内容页面
- 设置最低分数阈值（< 0.6 不返回），避免返回完全不相关的片段
- 引入 BM25 关键词检索，精确匹配标准号和专业术语
- 通过 RRF 融合向量 + BM25 结果，提升排序质量
- 保持向后兼容

**Non-Goals:**
- 不更换 embedding 模型（可能后续独立优化）
- 不改变文档分块策略（可能后续独立优化）
- 不引入外部 reranker（留给未来改进）

## Decisions

### Phase A — 自定义 VectorIndexRetriever

```python
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=5,
    filters=MetadataFilters(
        filters=[
            # 过滤掉封面页 (p1 = 封面, p5 = 前言)
            ExactMatchFilter(key="page_label", value="p1", operator="!="),
            ExactMatchFilter(key="page_label", value="p5", operator="!="),
            # 过滤起草人名单页
            ExactMatchFilter(key="page_label", value="ocr", operator="!="),
        ]
    ),
)

nodes = retriever.retrieve(query)
# 手工过滤低分节点
nodes = [n for n in nodes if n.score and n.score > 0.6]
```

选择 `VectorIndexRetriever` 而非直接操作 VectorStore，因为：
- Retriever 返回的 `NodeWithScore` 包含完整的 metadata 和 score
- 与 LlamaIndex 的 `RetrieverQueryEngine` 自然集成
- 后续可以无缝叠加 BM25 组合

页面类型判断依据：
- `page_label="p1"` → 封面页（标准的第 1 页，只有标题和标准号）
- `page_label="p5"` → 前言页（标准的第 5 页，GB 标准的 boilerplate）
- `page_label="ocr"` → 扫描件 OCR 全内容（可能混合无意义文本）

### Phase B — BM25 混合检索 + RRF

```
┌─────────────────────────────────────────────────────┐
│                    RetrieverQueryEngine              │
│                         │                            │
│              ┌──────────┴──────────┐                │
│              ▼                     ▼                 │
│     VectorIndexRetriever    BM25Retriever            │
│     (chroma + embedding)    (jieba tokenizer)        │
│              │                     │                 │
│              └──────────┬──────────┘                 │
│                         ▼                            │
│          Reciprocal Rank Fusion                      │
│          (score = 1/(k + rank_v) + 1/(k + rank_b))  │
│                         │                            │
│                         ▼                            │
│               Top-5 排序结果                          │
└─────────────────────────────────────────────────────┘
```

**BM25Retriever** 使用：
```python
from llama_index.core.retrievers import BM25Retriever

bm25_retriever = BM25Retriever.from_defaults(
    nodes=nodes,  # 从 index 中提取所有节点
    similarity_top_k=5,
)
```

**RRF 融合公式**：`score(d) = 1/(k + rank_v(d)) + 1/(k + rank_b(d))`，其中 `k=60` 为 RRF 常数值。

**自定义混合 Retriever**：
```python
class HybridRetriever(BaseRetriever):
    def __init__(self, vector_retriever, bm25_retriever):
        self._vector = vector_retriever
        self._bm25 = bm25_retriever

    def _retrieve(self, query):
        vec_nodes = self._vector.retrieve(query)
        bm25_nodes = self._bm25.retrieve(query)
        return self._rrf_fusion(vec_nodes, bm25_nodes)
```

### ChromaDB 和 BM25 索引同步

BM25 索引基于内存中的 `nodes` 构建。当 KB 重新索引时，BM25 索引需要重建。策略：延迟重建——每次检索时检查 nodes hash，若 KB 版本变化则重建。

## Data Flow

```
用户查询 "光伏电池的主要材料"
         │
         ▼
  Phase A: VectorIndexRetriever + MetadataFilters
         │  过滤掉 p1(封面), p5(前言), ocr(扫描)
         │  删除 score < 0.6 的节点
         ▼
  Phase B: BM25Retriever (jieba分词)
         │  精确匹配 "光伏 电池 材料 硅"
         ▼
  RRF 融合 → 重排序 → Top-5 → LLM 生成
```

## Risks / Trade-offs

- **[Risk] BM25 对中文分词依赖大**：jieba 分词质量直接影响 BM25 效果。→ 可接受，jieba 是中文 BM25 的事实标准。
- **[Risk] BM25 索引占用内存**：当前 108 个块约 80KB 文本，BM25 索引 ~5MB。在 100 个知识库规模下约 ~500MB。→ 可接受，且可采用惰性加载。
- **[Risk] MetadataFilters 硬编码页面号**：不同 PDF 的页面结构可能不同。→ 初始硬编码，后续可改为启发式检测（检测标题/标准号模式）。
- **[Risk] 检索速度下降**：从一次向量查询变为向量 + BM25 + 融合三步。→ 实测 BM25 为亚毫秒级，总延迟增加 < 10ms。

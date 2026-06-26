## Why

当前 RAG 检索质量存在三个问题：(1) 评分坍缩——所有块评分集中在 0.59~0.60，模型几乎无法区分相关与不相关内容；(2) 无意义片段污染结果——封面页、前言、目录、起草人名单等无内容页面频繁出现在前 5 条中；(3) 纯向量检索对精确关键词（标准号、专业术语）不敏感，导致用户看到与问题完全无关的来源。

## What Changes

- **Phase A — 自定义检索器**：用 `VectorIndexRetriever` + `MetadataFilters` 替代当前的 `index.as_query_engine()` 直接调用。过滤掉封面/前言/目录等无内容页面（通过 `page_label` 或 `file_path` 特征判断）；添加最低分数阈值，低于 0.6 的块不返回。
- **Phase B — BM25 混合检索**：新增 `llama-index-retrievers-bm25` + `jieba` 依赖，为每个知识库构建 BM25 索引。查询时同时执行向量检索和 BM25 检索，通过 Reciprocal Rank Fusion (RRF) 融合排序。
- **重新索引**：Phase B 完成后需要对新依赖的知识库做一次 reindex 以重建分块元数据。
- **无破坏性变更**：现有同步聊天和 CLI 保持不变。

## Capabilities

### New Capabilities
- `custom-vector-retriever`: 带 MetadataFilters 和分数阈值的自定义向量检索器
- `bm25-hybrid-retrieval`: 基于 BM25 + 向量的混合检索，含 RRF 融合

### Modified Capabilities
- `streaming-chat-response`: 检索部分使用新的自定义检索器
- `session-chat`: 同步 chat() 也切换到新的检索器

## Impact

- **后端**：`app/modules/session/session_manager.py` 的 `chat_stream()` 和 `chat()` 方法中的检索逻辑替换为自定义检索器 + BM25 混合检索。
- **索引**：`app/modules/kb_manager/indexer.py` 的索引过程需记录更精确的 metadata（如页面类型标记），便于过滤。
- **依赖**：Phase B 新增 `llama-index-retrievers-bm25` + `jieba`。
- **性能**：BM25 索引驻留内存，每个 KB 约额外占用 ~10MB（基于当前 108 个块估算）。

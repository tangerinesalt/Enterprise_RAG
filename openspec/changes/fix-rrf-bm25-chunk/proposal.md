## Why

12 条测试全部证实 RRF 融合劣化检索排名（12/12），根因有两个：

1. **SentenceSplitter 合并块破坏 BM25 段落边界**：D2（数字化开户）在原始段落上 BM25 评分 #1/40（7.30 分），但被 SentenceSplitter 合并到 D1 块后，在 12 条 chunk 上仅作为 D1 块的附属内容存在——BM25 的精确关键词匹配优势被抹消了
2. **RRF 给 BM25 和向量等权**：bge-m3 对正常查询全部排 #1，而 BM25 波动大（#1~#12），RRF 等权平均把向量 #1 拉到 #3~#7。BM25 的不可靠源于对停用词级高频词（"是"、"什么"）的过匹配

## What Changes

- **BM25 索引改用原始段落边界**：不再使用 SentenceSplitter 合并后的 chunk，而是用 `\n\n` 分割的原始段落构建 BM25 索引。这恢复了 D2 等具体段落的精确关键词匹配能力
- **RRF 融合重加权**：将向量路径权重提高到 0.7~0.8，BM25 权重降到 0.2~0.3（或改为动态权重：当 BM25 最高分与次高分差异 >50% 时提升 BM25 权重）
- **备选方案**：如果加权 RRF 仍不稳定，则降级为纯向量路径（仅使用 VectorIndexRetriever + Reranker），完全移除 BM25 路径

## Capabilities

### New Capabilities

- `bm25-paragraph-index`: BM25 索引基于原始段落边界（`\n\n` 分割）而非 SentenceSplitter 合并 chunk

### Modified Capabilities

- `kb-ingestion`: BM25 索引数据源改为原始段落列表，与向量索引的 chunk 分离
- `session-chat`: RRF 融合改为加权融合（向量权重 > BM25 权重），或支持降级为纯向量路径

## Impact

- **app/modules/retrieval/retriever.py**：`_build_bm25_retriever` 从原始文件读取段落而非从 index docstore；`_rrf_fusion` 支持权重参数；`build_retriever` 支持禁用 BM25
- **app/modules/kb_manager/indexer.py**：BM25 原始段落数据持久化路径（可选，若不实时重建）
- **config/settings.py**：新增 `RETRIEVER_MODE`（hybrid/vector-only）配置项

## Why

当前 BM25 和向量检索使用不同的文本切片：向量用 SentenceSplitter(512/128) 合并后的 chunk，BM25 用源文件的 `\n\n` 段落或 PDF 按页分割。两套索引粒度不同、node_id 不同，导致 RRF 融合退化为"拼接"而非真正的交叉验证——不能做"两路都命中→加分"的经典 RRF 融合。

## What Changes

- BM25 索引改为使用**与向量索引完全相同的 TextNode 列表**（即 SentenceSplitter 分块后的 nodes），而非从源文件重新分割段落
- 两路检索使用相同 node_id，RRF 去重和双路径加分恢复生效
- 移除 `_load_kb_paragraphs` 和独立的段落级 BM25 构建逻辑
- BM25 构建时机从 `build_retriever` 调用时改为在向量索引写入 ChromaDB 时同步持久化 BM25 索引数据

## Capabilities

### Modified Capabilities

- `bm25-paragraph-index`: 改为 `bm25-chunk-index`，BM25 构建数据源从源文件段落改为向量索引的 chunk nodes
- `kb-ingestion`: 索引时同步持久化 BM25 索引（与向量索引写入同一批 nodes）
- `session-chat`: RRF 融合恢复经典的 node_id 级交叉验证

## Impact

- **app/modules/retrieval/retriever.py**：`_build_bm25_retriever` 不再从源文件读取段落，改为接收 nodes 列表；移除 `_load_kb_paragraphs`
- **app/modules/kb_manager/indexer.py**：在 `index_file` 中将分块后的 nodes 列表持久化到 BM25 缓存，或实时传入 `_build_bm25_retriever`
- **app/modules/session/session_manager.py**：`build_retriever` 调用时传入 chunks nodes（可从 index 提取或从缓存读取）

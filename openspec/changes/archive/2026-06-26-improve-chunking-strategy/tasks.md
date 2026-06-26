## 1. 配置项

- [x] 1.1 在 `config/settings.py` 中新增分块配置项：`CHUNK_SIZE=512`, `CHUNK_OVERLAP=128`, `CHUNK_PARAGRAPH_SEPARATOR="\n\n"`

## 2. 页面类型检测

- [x] 2.1 在 `app/modules/kb_manager/indexer.py` 中创建 `_detect_page_type(page_label, text)` 函数，实现启发式规则（cover/toc/foreword/ocr_scanned/content）

## 3. 索引流程重写

- [x] 3.1 在 `indexer.py` 的 `index_file()` 中增加 `SentenceSplitter` 自定义配置，用 `parser.get_nodes_from_documents()` 替代默认分块
- [x] 3.2 为每个 TextNode 注入 metadata：`page_type`, `page_label`, `chunk_index`, `total_chunks`, `file_path`
- [x] 3.3 使用 `VectorStoreIndex(nodes=nodes, storage_context=storage_context)` 替代 `VectorStoreIndex.from_documents(documents, ...)`
- [x] 3.4 验证：重新索引后块大小 avgt=428 字符，page_type 完整（cover/toc/foreword/content）

## 4. 检索器适配

- [x] 4.1 修改 `app/modules/retrieval/retriever.py` 的 `build_retriever()`：将 `MetadataFilters` 从 `page_label` 硬编码改为 `page_type` 过滤
- [x] 4.2 验证：使用 `page_type` 过滤后，封面/目录/前言页不再出现在检索结果中

## 5. 测试

- [x] 5.1 重新索引一个现有 KB，确认分块质量
- [x] 5.2 执行一次端到端检索 + 问答，确认结果质量提升

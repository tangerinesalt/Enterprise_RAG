## 1. 索引幂等：先删后增

- [x] 1.1 在 `indexer.py` 的 `index_file()` 中，调用 `delete_vectors(kb_name, filename)` 作为前置清理步骤
- [x] 1.2 修改 `index_folder()` 和 `index_all()`：不再直接批量写入，改为逐个文件调用 `index_file()` 以继承幂等逻辑

## 2. BOM 消除

- [x] 2.1 在 `chunker.py` 的 `chunk_documents()` 中，对每个 `doc.text` 执行 `.lstrip('﻿')` 去除 BOM

## 3. 分数阈值调低

- [x] 3.1 在 `retriever.py` 中将 `_ScoreThresholdRetriever` 默认 threshold 从 0.6 改为 0.2

## 4. Source 文本取消截断

- [x] 4.1 在 `session_manager.py` 的 `chat_stream()` 中，将 `node.text.strip()[:300]` 改为 `node.text.strip()`
- [x] 4.2 在 `session_manager.py` 的 `chat()` 中，同步修改相同的 `[:300]` 截断逻辑

## 5. 验证：重建索引并确认修复

- [x] 5.1 对 `kb/062500` 执行重新索引，向量数从 48 → 13（唯一 chunk），重复消除
- [x] 5.2 查询 "A1是什么"，sources 中不再出现重复条目（13 条唯一向量）
- [x] 5.3 查询 "A1是什么"，sources 中不再包含 `﻿` BOM 字符
- [x] 5.4 通过完整混合检索（top_k=12），A1 出现在 RRF #6 → Reranker #4（score 0.5787）

## Why

通过实机测试确认当前 RAG 系统存在 4 个严重检索质量问题：ChromaDB 重复索引导致 65% 的向量为重复条目；`_ScoreThresholdRetriever(0.6)` 阈值过高导致向量路径始终为空；源文件 BOM 字符未经处理污染向量数据；source 文本截断 300 字符导致 LLM 接收的上下文不完整。这些问题共同导致检索准确率低下，用户反复提问也无法获得正确答案。

## What Changes

- **修复重复索引**：索引前清理 ChromaDB 中该文件的旧向量（`index_all`/`index_folder` 也做清理），或在索引时去重
- **移除/调低分数阈值**：将 `_ScoreThresholdRetriever` 的 threshold 从 0.6 降至 0.3 或移除（当前 embedding 最高分仅 0.48）
- **修复 BOM 污染**：文档解析阶段（PDF/TXT）统一用 `utf-8-sig` 编码读取，或在 chunker 中 strip BOM
- **取消 sources 截断**：将 `node.text.strip()[:300]` 改为完整文本（至少放大到 1024 或直接不截断）

## Capabilities

### New Capabilities

- `kb-index-dedup`: 知识库索引时自动清理旧向量，避免重复

### Modified Capabilities

- `kb-ingestion`: 文档解析阶段增加 BOM 清理；索引新增幂等性（先删旧数据再写新数据）
- `session-chat`: 检索管线移除/调低 0.6 分数阈值；取消 source 文本 300 字符截断

## Impact

- **app/modules/kb_manager/indexer.py**：`index_file` 和 `index_all`/`index_folder` 增加前置清理逻辑
- **app/modules/retrieval/retriever.py**：`_ScoreThresholdRetriever` threshold 调整或移除
- **app/modules/kb_manager/chunker.py**：增加 BOM strip 步骤
- **app/modules/session/session_manager.py**：source 文本截断从 300 改为不限或 1024

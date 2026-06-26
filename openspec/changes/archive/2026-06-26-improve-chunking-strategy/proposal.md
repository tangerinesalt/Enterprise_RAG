## Why

当前 `VectorStoreIndex.from_documents(documents)` 使用 LlamaIndex 默认的 `SentenceSplitter(chunk_size=1024, overlap=200)`，缺乏对中文标准 PDF 文档的适配。实际分块效果很差：块大小从 31 字符到 4962 字符不等，超大块（完整目录）导致嵌入向量模糊，超小块（页面碎片）几乎无语义，且无法给块打 metadata 标记。这直接导致检索时"评分坍缩"——所有块都在 0.59~0.60，模型无法区分相关与不相关内容。

## What Changes

- **自定义 NodeParser 组合策略**：在 `indexer.py` 中用 `from_nodes()` 替代 `from_documents()`，使用多层组合的 `SentenceSplitter` 进行更精细的文档切分。
- **企业级分块参数**：`chunk_size=512`, `chunk_overlap=128`，配合语义段落边界感知，确保块大小一致且内容聚焦。
- **节点级 Metadata 标记**：自动检测封面页、前言、目录、正文等页面类型，为后续 `MetadataFilters` 提供精确过滤依据。
- **配置化分块参数**：将 chunk_size、chunk_overlap 等参数提取到 `config/settings.py`，支持按知识库类型自定义。
- **需要重新索引**：现有 KB 需要做一次 reindex 才能应用新分块策略。

## Capabilities

### New Capabilities
- `custom-node-parser`: 基于 SentenceSplitter 的企业级组合分块策略，支持多层解析和 metadata 标记

### Modified Capabilities
- `kb-ingestion`: 索引流程从 `from_documents` 改为 `from_nodes`，分块参数可配置
- `custom-vector-retriever`: 新增页面类型 metadata 过滤条件

## Impact

- **后端**：`app/modules/kb_manager/indexer.py` 重写索引核心流程；`config/settings.py` 新增分块配置项。
- **重新索引**：所有现有知识库需要触发 reindex 才能应用新分块。
- **检索器适配**：`app/modules/retrieval/retriever.py` 的 `MetadataFilters` 配合新的页面类型标记。
- **无 API 变更**。

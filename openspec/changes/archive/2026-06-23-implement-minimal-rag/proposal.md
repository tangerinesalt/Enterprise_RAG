## Why

目标是理解 RAG 路线，而不是直接构建完整项目。通过创建简单的示例脚本，在 `example/` 文件夹中实现最小 RAG 链路，直观地展示"解析→分块→向量化→存储→检索→生成"的完整流程。

## What Changes

- 创建 `example/` 目录，存放最小 RAG 示例代码
- **Part 1 — 解析 + 索引 (parse_index.py)**：读取文档 → 提取文本 → 分块 → Embedding → 存入 ChromaDB
- **Part 2 — 检索 + 生成 (retrieve_generate.py)**：输入问题 → 向量检索 → 注入 LLM → 生成回答
- 提供一份测试文档用于验证流程
- 一份简单的 README 说明运行步骤

## Capabilities

### New Capabilities
- `rag-pipeline-demo`: 两个 Python 脚本，串联完整的 RAG 数据流，重点是可读性和教学性

### Modified Capabilities

- 无

## Impact

- 新增 `example/` 目录，独立于主项目代码
- 依赖：`chromadb`、`pypdf`、`requests`（通过 Ollama HTTP API，无需额外 SDK）
- 不修改现有项目结构（`app/`、`config/` 等保持不变）

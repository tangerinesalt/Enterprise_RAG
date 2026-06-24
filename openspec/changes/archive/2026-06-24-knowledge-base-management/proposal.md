## Why

目前项目的 RAG 功能只有零散的示例脚本（example/01/、02/），缺乏统一的知识库管理能力。需要将文档接入、向量化、索引流程工程化，实现可按名称创建/管理的知识库，为后续构建企业级 RAG 应用奠定基础。

## What Changes

- 新增 `kb/` 根目录，作为所有知识库的存储根
- 实现知识库管理模块：
  - `kb create <name>` — 按名称创建知识库（自动初始化向量数据库 + 文件副本目录）
  - `kb upload <kb_name> <file_path>` — 上传文件到知识库（保存同名副本 + 向量化索引）
  - `kb delete <kb_name> <filename>` — 从知识库删除文件副本和对应向量
  - `kb reindex <kb_name> <filename>` — 对已有副本重新索引（增量更新向量）
  - `kb list <kb_name>` — 列出知识库中的文件
- 每个知识库内部结构：
  ```
  kb/
  └── <kb_name>/
      ├── files/              # 上传的文件副本（同名保存）
      └── vector_db/          # ChromaDB 持久化目录
  ```
- 基于 llama_index 实现文档解析、分块、Embedding、索引
- 提供 `test_retrieve.py` 测试接口（放在 `test/` 下，归档时删除）

## Capabilities

### New Capabilities

- `kb-management`: 知识库的创建、文件上传、文件删除、重新索引等管理操作
- `kb-ingestion`: 基于 llama_index 的文档解析、分块、向量化与索引流程
- `kb-retrieval-test`: 简易检索测试接口，用于验证知识库功能

### Modified Capabilities

- 无（此为新功能）

## Impact

- 新增 `app/kb_manager/` 模块 — 知识库管理核心代码
- 新增 `kb/` 根目录 — 知识库数据存储（自动创建，纳入 .gitignore）
- 新增 `test/test_retrieve.py` — 检索测试脚本（归档时删除）
- 复用 `example/02/` 中的 RobustPDFReader、OllamaEmbedding 等能力
- 修改 `settings.json` 或新增 `config/settings.py` 统一读取环境配置
- 依赖已就位：llama-index-core、chromadb、pypdf、requests

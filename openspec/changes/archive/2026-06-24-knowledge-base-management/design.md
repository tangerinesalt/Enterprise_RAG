## Context

项目目前有 example/01/（纯手写 RAG）和 example/02/（LlamaIndex RAG）两个示例，已验证 RAG 链路可行。现在需要将能力工程化为可管理的知识库系统。

Ollama 已本地运行（qwen3-embedding:4b 做 Embedding，qwen3.5:9b 做生成），依赖已就位。

## Goals / Non-Goals

**Goals:**
- 实现知识库 CRUD：创建、上传、删除、重新索引
- 知识库使用文件系统目录结构管理，自包含（向量库 + 文件副本）
- 基于 llama_index 实现文档解析、分块、Embedding、索引
- 提供 CLI 管理接口
- 提供测试检索接口验证功能

**Non-Goals:**
- 不做多用户/权限隔离（当前为单用户）
- 不做 Web UI（后续阶段添加）
- 不做分布式部署
- 不做增量实时同步（全量重新索引即可）

## Decisions

### 1. 知识库存储结构

```
kb/
└── <kb_name>/
    ├── files/              # 文件副本（同名保存）
    │   ├── document1.pdf
    │   └── document2.txt
    └── vector_db/          # ChromaDB 持久化目录
```

- **理由**：自包含，迁移/备份只需复制一个目录；文件同名便于追踪。
- **替代方案**：元数据数据库记录文件映射 → 增加复杂度，MVP 不需要。

### 2. CLI 作为管理入口

`python -m app.kb_manager.cli <command> <args>`

| 命令 | 功能 |
|------|------|
| `kb create <name>` | 创建知识库 |
| `kb upload <name> <file>` | 上传并索引文件 |
| `kb delete <name> <filename>` | 删除文件及向量 |
| `kb reindex <name> <filename>` | 重新索引文件 |
| `kb list <name>` | 列出文件 |
| `kb list` | 列出所有知识库 |

- **理由**：开发快，便于测试和集成到后续的 FastAPI。

### 3. 基于 llama_index 的索引流程

复用 example/02/ 中的 RobustPDFReader + OllamaEmbedding：

```
upload file → 复制到 kb/<name>/files/
           → SimpleDirectoryReader 读取
           → Text splitter 分块
           → OllamaEmbedding 向量化
           → ChromaVectorStore 存储（kb/<name>/vector_db/）
```

- **理由**：已有验证，llama_index 分块/Embedding 封装完善。
- 每个知识库使用独立的 ChromaDB PersistentClient（不同 path）。

### 4. 文件删除 = 删除副本 + 删除向量

删除文件时：
1. 删除 `kb/<name>/files/<filename>`
2. 从 ChromaDB 中删除该文件来源的所有向量（通过 metadata 中的 file_name 过滤）

重新索引时：
1. 删除原向量
2. 重新解析文件 → Embedding → 存储

## 模块结构

```
app/kb_manager/
├── __init__.py              # KnowledgeBase 类
├── cli.py                   # CLI 入口
└── indexer.py               # 文档解析 + 索引（复用 example/02/ 能力）
```

## Data Flow

```
用户 CLI
  │
  ├─ kb create <name>
  │   → 创建 kb/<name>/files/  +  kb/<name>/vector_db/
  │
  ├─ kb upload <name> <file>
  │   → 复制文件到 kb/<name>/files/
  │   → 解析 → 分块 → Embedding → ChromaDB
  │
  ├─ kb delete <name> <filename>
  │   → 删除 kb/<name>/files/<filename>
  │   → ChromaDB 按 file_name 过滤删除向量
  │
  ├─ kb reindex <name> <filename>
  │   → 删除原向量 → 重新解析 → Embedding → ChromaDB
  │
  └─ kb list [name]
      → 列出知识库 / 库内文件
```

## Risks / Trade-offs

- **[风险] 同名文件覆盖** → upload 时若同名文件已存在，覆盖文件副本并重新索引
- **[风险] ChromaDB 按 metadata 删除的性能** → MVP 单库文件数 < 100，可接受
- **[风险] 删除时向量不一致** → 原子操作：先删文件副本，再删向量

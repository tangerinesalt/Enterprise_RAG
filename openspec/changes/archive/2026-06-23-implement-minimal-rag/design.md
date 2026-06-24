## Context

项目的核心是理解 RAG 路线，而非工程化。通过两个独立但串联的 Python 脚本，在 `example/` 中演示完整流程，注重可读性和教学性。

Ollama 已本地运行（`http://127.0.0.1:11434/`），模型为 `qwen3.5:9b`。

## Goals / Non-Goals

**Goals:**
- 两个独立脚本，step-by-step 展示 RAG 流程
- 全部通过 Ollama HTTP API，零额外依赖
- 所有配置硬编码在脚本头部，一眼可见

**Non-Goals:**
- 不做模块化/工程化封装
- 不做 CLI 界面（直接运行脚本）
- 不做异常处理之外的健壮性设计
- 不写测试

## Decisions

### 1. 单脚本 vs 多脚本

- **选择**：两个独立脚本，分别对应 RAG 两阶段
- **理由**：理解和演示更清晰，可分别运行、单独观察每步输出

### 2. 同目录存储 ChromaDB

- **选择**：ChromaDB 持久化到 `example/rag_demo_db/`
- **理由**：自包含，删除 example 目录时不留残余

### 3. 所有参数写在脚本头部

- **选择**：OLLAMA_URL、MODEL、CHUNK_SIZE 等常量写在脚本顶部
- **理由**：无需额外配置文件，一眼可改

## 数据流

```
┌─ Part 1: parse_index.py ─────────────────────────────┐
│                                                        │
│  文档(.pdf/.txt/.md)                                   │
│       │                                                │
│       ▼                                                │
│  提取文本 ──→ 分块 ──→ Embedding (Ollama) ──→ ChromaDB │
│                                                       │
└───────────────────────────────────────────────────────┘

┌─ Part 2: retrieve_generate.py ───────────────────────┐
│                                                        │
│  用户问题                                              │
│       │                                                │
│       ▼                                                │
│  Embedding (Ollama) ──→ ChromaDB 检索 ──→ 拼接 Prompt │
│                                                   │    │
│                                                   ▼    │
│                                        LLM (Ollama)    │
│                                                   │    │
│                                                   ▼    │
│                                            生成回答     │
│                                            + 来源引用   │
└───────────────────────────────────────────────────────┘
```

## 文件结构

```
example/
├── README.md              # 运行说明
├── sample.txt             # 测试文档
├── parse_index.py         # Part 1: 解析 + 索引
└── retrieve_generate.py   # Part 2: 检索 + 生成
```

## 脚本内部流程

### parse_index.py

```python
# 配置（脚本顶部）
OLLAMA_URL = "http://127.0.0.1:11434"
EMBED_MODEL = "qwen3.5:9b"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
DB_PATH = "./rag_demo_db"

# 流程（带过程打印）
1. 读取文档 → 打印文档长度
2. 分块 → 打印块数
3. 逐块 Embedding → 打印向量维度
4. 存入 ChromaDB → 打印"索引完成"
```

### retrieve_generate.py

```python
# 配置（脚本顶部）
OLLAMA_URL = "http://127.0.0.1:11434"
EMBED_MODEL = "qwen3.5:9b"
LLM_MODEL = "qwen3.5:9b"
DB_PATH = "./rag_demo_db"
TOP_K = 5

# 流程（带过程打印）
1. 接收用户问题
2. 问题 Embedding
3. ChromaDB 检索 → 打印检索结果片段
4. 构建 RAG Prompt
5. 调用 Ollama Chat → 打印回答 + 来源
```

## Risks / Trade-offs

- Qwen3.5:9b 的 Embedding 维度需首次调用后确认（影响 ChromaDB 集合初始化）
- ChromaDB 首次运行会自动创建集合，须确保维度参数正确
- 测试文档不宜过大（< 50KB），否则首次 Embedding 等待时间较长

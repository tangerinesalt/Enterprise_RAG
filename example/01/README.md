# RAG 最小示例

两个脚本展示完整的 RAG 链路：**文档解析 → 分块 → Embedding → 检索 → LLM 生成**

## 前置条件

```bash
# 1. 安装依赖
pip install chromadb pypdf requests

# 2. 确保 Ollama 运行
#    需要模型：
#    - qwen3-embedding:4b（Embedding）
#    - qwen3.5:9b（LLM 生成）
curl http://127.0.0.1:11434/api/tags
```

## 运行

### Part 1: 解析 + 索引

```bash
python parse_index.py sample.txt
# 或使用自己的文件（支持 .txt / .md / .pdf）
python parse_index.py 你的文档.pdf
```

预期输出：
```
RAG 索引流程 -- Part 1: 解析 + 索引

[1/4] 读取文档: sample.txt
      [OK] 提取到 1,211 个字符
[2/4] 文本分块 (size=500, overlap=50)
      [OK] 生成 3 个文本块
[3/4] 向量化 (模型: qwen3-embedding:4b)
      [OK] 向量维度: 2560
      [OK] 共 3 个向量
[4/4] 存入 ChromaDB
      [OK] 成功索引 3 个文本块

索引完成！共 3 个块，向量维度 2560
```

### Part 2: 检索 + 生成

```bash
python retrieve_generate.py "什么是RAG？它有哪些优势？"
```

预期输出包含：
- 检索到的相关片段及相似度分数
- LLM 基于文档生成的回答
- 来源标注 `[来源 1]`、`[来源 2]` 等
- 完整的参考来源原文

## 自定义配置

两个脚本顶部的常量可直接修改：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Ollama 地址 |
| `EMBED_MODEL` | `qwen3-embedding:4b` | Embedding 模型 |
| `LLM_MODEL` | `qwen3.5:9b` | 生成模型（仅 Part 2） |
| `CHUNK_SIZE` | `500` | 分块字符数（仅 Part 1） |
| `CHUNK_OVERLAP` | `50` | 块间重叠字符数（仅 Part 1） |
| `TOP_K` | `5` | 检索返回结果数（仅 Part 2） |

## RAG 流程示意

```
┌─ parse_index.py ──────────────────────────────────┐
│                                                     │
│  文档 → 提取文本 → 分块 → Embedding(Ollama) → ChromaDB │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─ retrieve_generate.py ────────────────────────────┐
│                                                     │
│  问题 → Embedding → ChromaDB检索 → RAG Prompt → LLM │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 目录结构

```
example/
├── README.md               # 本文件
├── sample.txt              # 测试文档
├── parse_index.py          # Part 1: 解析 + 索引
├── retrieve_generate.py    # Part 2: 检索 + 生成
└── rag_demo_db/            # ChromaDB 持久化目录（自动生成）
```

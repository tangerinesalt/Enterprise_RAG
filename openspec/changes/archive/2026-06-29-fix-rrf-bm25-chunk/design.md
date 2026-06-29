## Context

当前 BM25 索引构建方式：从 `index.docstore.docs` 中提取 VectorStoreIndex 已分块的 nodes，即经过 SentenceSplitter(512/128) 合并后的 chunk。测试证明这种合并破坏了原始段落边界，导致 BM25 损失了精确关键词匹配能力。

RRF 融合当前等权处理向量和 BM25 结果（`1/(k+rank+1)` 各加一次）。测试证明 12/12 情况下 RRF 劣化了向量路径的原始排名。

## Goals / Non-Goals

**Goals:**
- BM25 使用原始段落（`\n\n` 分割的节）而非 SentenceSplitter chunk 作为索引单元
- RRF 融合支持向量/BM25 权重系数，默认为 0.7/0.3
- 支持纯向量模式（`vector-only`），跳过 BM25 路径和 RRF 融合
- 与现有 session 配置兼容（`top_k`, `top_n` 仍然有效）

**Non-Goals:**
- 不修改向量索引的 chunking 策略（SentenceSplitter 512/128 对向量检索已足够好）
- 不新增外部依赖
- 不做自动模式切换（由配置手动选择）

## Decisions

### 1. BM25 索引：从源文件重建原始段落列表

`_build_bm25_retriever` 改为：
- 通过 KnowledgeBase 读取知识库源文件目录
- 按文件类型区分段落分割策略：
  - `.txt` / `.md`：按 `\n\n` 分割为段落（来源可靠）
  - `.pdf`（PyPDF 路径）：按 `page_label` metadata 分页，每页作为独立单元；页内超长文本（>1024 字符）尝试 `\n\n` 二次分割
  - `.pdf`（OCR 路径）：不分割，OCR 文本已碎片化
- 构建独立的 BM25 索引，与向量索引的 chunk 无关
- 按 kb_name 缓存（已有缓存机制）

**理由**：原始段落是自然的语义单元，"数字化开户" 作为一个完整段落被独立索引，BM25 的关键词匹配才能发挥优势。PDF 的页边界是比 `\n\n` 更可靠的天然分割点。

### 2. RRF 加权融合

`_rrf_fusion` 新增参数：
```
_rrf_fusion(vector_nodes, bm25_nodes, top_k=5, k=60, vector_weight=0.7, bm25_weight=0.3)
```

评分公式：
```
score = vector_weight * 1/(k+vec_rank+1) + bm25_weight * 1/(k+bm25_rank+1)
```

默认权重 0.7/0.3 基于测试数据：bge-m3 对正常查询全部 #1，BM25 波动大。向量权重 0.7 可确保在 BM25 排名差时（如 A1/B1 查询 BM25 #9~#12）向量路径的 #3 排名不被拉低超过 1-2 位。

### 3. 纯向量模式

`build_retriever` 新增参数 `mode='hybrid'`，可选 `'vector-only'`。`vector-only` 时跳过 BM25 构建和 `_HybridRetriever`，直接返回 `threshold_retriever`（VectorIndexRetriever + 0.2 阈值）。

### 4. 配置入口

新增 `retriever_mode` 字段到会话 `config.json`，与已有的 `top_k`/`top_n` 并列。默认 `"hybrid"`，可选 `"vector-only"`。

```json
// sessions/<name>/config.json
{
  "kb_name": "my_kb",
  "top_k": 8,
  "top_n": 5,
  "retriever_mode": "hybrid"    // "hybrid" | "vector-only"
}
```

沿用已有的 CLI `session config` 子命令和 API `PATCH /api/session/{name}/config`，无需新增路由：

```bash
python -m app.cli session config my-session --set retriever_mode=vector-only
```
```http
PATCH /api/session/my-session/config  {"retriever_mode": "vector-only"}
```

## Risks / Trade-offs

- **[兼容性] 旧 KB 无原始段落缓存** → BM25 实时从源文件重建（每个文件用 `\n\n` 分割），不需要持久化
- **[内存] 原始段落数可能多于 chunk 数** → 当前 4 文件共 ~40 段落，远小于 BM25 内存上限
- **[纯向量模式] 放弃 BM25 对精确关键词的召回** → BM25 在短查询和专有名词场景下仍有价值（如 B1 在 BM25 排 #1）。纯向量模式作为可选项而非默认值

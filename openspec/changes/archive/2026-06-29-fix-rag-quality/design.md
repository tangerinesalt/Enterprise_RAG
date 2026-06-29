## Context

当前 RAG 系统通过测试确认存在 4 个检索质量问题：

1. **重复索引**: ChromaDB 48 条向量中仅 17 条唯一（65% 重复），`index_all`/`index_file` 每次调用都在原 collection 追加，未清理同名文件旧数据
2. **阈值过高**: `_ScoreThresholdRetriever(threshold=0.6)` 过滤全部向量结果（当前 embedding 模型最高分仅 0.488），导致混合检索退化为纯 BM25
3. **BOM 污染**: 源文件含 UTF-8 BOM，`SimpleDirectoryReader` 以默认编码读取保留 BOM，嵌入到所有向量中
4. **Source 截断**: `node.text.strip()[:300]` 丢失 20-40% 的 chunk 内容

## Goals / Non-Goals

**Goals:**
- 索引幂等：无论调用多少次 `index_file`/`index_all`，ChromaDB 中每个文件的数据唯一
- 阈值合理化：`_ScoreThresholdRetriever` 不再完全阻断向量路径
- 消除 BOM：最终落库的向量文本不含 BOM 字符
- 完整 source：LLM 收到的检索片段不被硬截断

**Non-Goals:**
- 不改变 embedding 模型（仍用 qwen3-embedding:4b）
- 不改变分块策略（仍用 SentenceSplitter 512/128）
- 不重构检索器架构（仍用 Vector+BM25+RRF+Rerank）

## Decisions

### 1. 索引幂等：先删后增

`index_file` 方法在写入新向量前，按 `file_path` metadata 删除该文件的已有向量。  
`index_all`/`index_folder` 改为逐个文件调用 `index_file`（而非批量直接写），继承其清理逻辑。  
**理由**：ChromaDB 的 `delete(where={file_path: ...})` 已经支持按 metadata 过滤删除，无需引入外部 dedup 方案。

### 2. 阈值调整：从 0.6 降至 0.3

当前 `qwen3-embedding:4b` 的相似度分数分布大约在 0.15-0.50 之间，0.3 作为下限可以过滤最不相关的尾部，同时保留向量路径的有效性。  
**替代方案考虑**：
- 完全移除阈值 → 所有噪声进入 RRF，可能压低相关片段的排名
- 动态阈值（基于分数分布自动计算）→ 复杂度高，不适合 MVP
- 选择 0.3 的理由：测试中 A1 的分数为 0.243，0.3 仍会过滤掉 A1。为让至少部分 A 系列进入，实际上可能需要阈值更低。A 文件中 A6 最高分 0.488，A1 只有 0.243。**更合理的做法是降到 0.2 或完全移除，让 RRF + Reranker 承担过滤职责。**

**最终决定**：降低 threshold 到 0.2（或设可配置参数，默认 0.2），同时允许负值或 0 表示"不启用阈值"。

### 3. BOM 消除：在 chunker 中做全局 strip

在 `chunker.py` 的 `chunk_documents` 中，对所有 doc.text 执行 `.lstrip('﻿')`。  
**理由**：
- 比修改 IndexReader 覆盖面更广（无论哪种 Reader，最终都经过 chunker）
- 单点修改，不影响上游加载逻辑

### 4. Source 截断：从 300 改为不限

`session_manager.py` 的 `chat_stream` 和 `chat` 方法中 `node.text.strip()[:300]` 改为 `node.text.strip()`，不再截断。  
若担心 context window 过大，可考虑以 chunk_size 为上限（512）。  
**理由**：LLM 自身的 context window（如 qwen3.5:9b 的 32K）远超当前 chunk 长度，截断无安全收益。

## Risks / Trade-offs

- **[重建索引] 旧 KB 中已存在的重复/BOM 数据不会自动修复** → 需要手动执行一次重新索引
- **[阈值 0.2 过滤 A1] A1 的分数 0.243 在 0.2 以上** → 阈值降到 0.2 后 A1 能通过，但仍在 top-8 的末尾。根本上需要通过提升 embedding 质量或放大 top_k 解决
- **[source 不截断] 极端长文本可能撑大 LLM token 消耗** → 当前 chunk_size=512，最坏情况 12 个 source × 512 = 6K tokens，完全可以接受

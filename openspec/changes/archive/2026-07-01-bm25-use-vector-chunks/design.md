## Context

当前 BM25 从源文件按 `\n\n` 或 PDF 按页构建独立段落索引，向量从 SentenceSplitter 合并 chunk 构建。两套索引粒度不同、node_id 不同，RRF 的去重逻辑不生效、双路径加分无法实现。

`build_retriever` 已传入 `index`（VectorStoreIndex），但 `index.docstore` 在 ChromaDB 模式下为空。ChromaDB 的 document ID 实际上就是 llama_index 的 node_id。

## Goals / Non-Goals

**Goals:**
- BM25 和向量索引使用完全相同的 chunk 文本（同一批 TextNode，相同 node_id）
- RRF 的 `node_id` 去重生效，双路径加分恢复
- 不修改 indexer.py，不改动现有索引流程

**Non-Goals:**
- 不改变 chunk 策略（仍用 SentenceSplitter 512/128）
- 不改变 BM25 的 tokenizer 或参数
- 不改变加权 RRF 的权重（仍为 0.7/0.3）

## Decisions

### 1. BM25 从 ChromaDB 读取 chunk 文本（无需新索引）

`_build_bm25_retriever` 直接从知识库的 ChromaDB collection 读取已存储的 chunk 文本和 node_id：

```python
data = chroma_collection.get(include=["documents"])
nodes = [TextNode(text=t, node_id=did) 
        for did, t in zip(data["ids"], data["documents"])]
```

ChromaDB 的 document ID 就是 llama_index 写入时的 node_id，所以重建的 TextNode 与向量索引完全一致。

### 2. RRF 恢复 node_id 级去重

BM25 和向量使用相同 node_id 后，`_rrf_fusion` 的 `seen` 去重和 `rank_scores` 双路径加分恢复正常。

### 3. 保留 `_load_kb_paragraphs` 的 PDF 支持代码（不移除）

保留函数但不主动调用，供按页分割的独立场景使用。BM25 默认走 ChromaDB chunk 路径。

## Risks / Trade-offs

- **[短查询退化] 段落级 BM25 对短查询更精确（如"A1"）** → chunk 级 BM25 将 A1~A3 合并，关键词 IDF 被稀释。但加权 RRF (0.7向量) 可抵消此影响
- **[ChromaDB 读取开销] 每次构建 BM25 都读一次全量 chunk 文本** → 已有 kb_name 级缓存，只需首次读取；ChromaDB `get()` 比读源文件快

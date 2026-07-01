## 1. BM25 从 ChromaDB 读取 chunk 文本

- [x] 1.1 `_build_bm25_retriever` 改为从 ChromaDB collection 读取 `ids` + `documents`，构建相同 node_id 的 TextNode 列表（先创建 TextNode，再赋值 `node.node_id` 覆盖）
- [x] 1.2 保留 `_load_kb_paragraphs` 函数定义（不再调用）
- [x] 1.3 `_build_bm25_retriever` 直接从 KnowledgeBase 获取 ChromaDB 路径，不需要 index 参数

## 2. RRF 去重验证

- [x] 2.1 RRF 结果数 = 12（12 向量 + 12 BM25 → 12 唯一 → 去重生效）
- [x] 2.2 所有 chunk 均为 `[v+b]` 双路径，得分 = 0.7/(k+rank+1) + 0.3/(k+rank+1)

## 3. 验证

- [x] 3.1 12 条查询：11/12 命中（"量化投资"受 reranker 限制），与优化前一致
- [x] 3.2 node_id 交集: 12/12 ✓
- [x] 3.3 RRF 结果 ≤12，无重复

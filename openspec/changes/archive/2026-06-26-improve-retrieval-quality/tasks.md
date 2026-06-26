## 1. Phase A — 自定义向量检索器

- [x] 1.1 在 `app/modules/session/session_manager.py` 中创建 `_build_retriever(index, kb_name)` 方法：
  - 使用 `VectorIndexRetriever` 替代 `index.as_query_engine()`
  - 配置 `MetadataFilters` 过滤 `p1`（封面）、`p5`（前言）、`ocr`（扫描）
  - 设置 `similarity_top_k=5`
- [x] 1.2 在 `chat_stream()` 和 `chat()` 中替换检索逻辑：
  - 用 `_build_retriever()` + `retriever.retrieve(query)` 替代当前的 `query_engine.query(query)`
  - 手动过滤 `score < 0.6` 的节点
  - 将过滤后的 nodes 传给 LLM 生成
- [x] 1.3 验证：重新查询"光伏电池的主要材料"，确认封面/前言页不再出现，低分块被过滤

## 2. Phase B — BM25 混合检索

- [x] 2.1 安装依赖：`pip install llama-index-retrievers-bm25 jieba`
- [x] 2.2 在 `_build_retriever()` 中增加 BM25 检索分支：
  - 从 index 提取所有 nodes
  - 使用 `BM25Retriever.from_defaults()` 构建 BM25 索引
  - 缓存 BM25 索引（按 kb_name），lazy rebuild
- [x] 2.3 实现 `_rrf_fusion(vector_nodes, bm25_nodes, k=60)` 方法：
  - 计算 RRF 分数并合并排序
  - 返回 Top-5
- [x] 2.4 创建 `HybridRetriever` 类继承 `BaseRetriever`：
  - vector 检索 + BM25 检索 + RRF 融合
  - 处理一方无结果的降级
  - 集成 `MetadataFilters`
- [x] 2.5 验证：查询"光伏组件安全要求 GB/T"，确认 BM25 精确匹配到相关标准号

## 3. 验证与修复

- [x] 3.1 验证同步 `chat()` 和流式 `chat_stream()` 行为一致
- [x] 3.2 验证没有知识的查询返回"未找到相关信息"而非无关片段

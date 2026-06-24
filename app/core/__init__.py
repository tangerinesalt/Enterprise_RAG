"""核心业务逻辑层。

各子模块对应 RAG 链路中的关键阶段：
  ingestion/  → 文档接入、格式解析、文本提取
  chunking/   → 文本分块策略
  embedding/  → 向量化（Embedding 模型调用）
  retrieval/  → 向量检索、语义搜索、相关性排序
  generation/ → 检索结果注入 LLM、生成回答
"""

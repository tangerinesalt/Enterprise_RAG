## Why

本次 A1 追踪测试暴露了 RAG 管线中多个难以通过人工观察发现的深层次问题（embedding 余弦相似度全为负数、RRF 排名与语义相关性脱节、阈值过滤阻断路径）。需要将这次诊断方法沉淀为可重复执行的测试套件，以便：

1. 未来修改任何检索参数（top_k、threshold、reranker 模型）后快速评估影响
2. 更换 embedding 模型（如从 qwen3-embedding:4b 切换）时量化对比效果
3. 每次索引重建后检查向量质量，防止退化

## What Changes

- 在 `test/` 下创建 `test_retrieval_diagnostic.py`：结构化的检索管线诊断工具
- 支持命令行参数：`<kb_name> <query>`，可选 `--top-k` `--top-n` `--threshold`
- 输出每个阶段的评分排名（embedding cosine_sim、VectorIndexRetriever score、BM25 rank、RRF score、reranker score）
- 自动检测并告警：cosine_sim 全负数、阈值过滤率过高、重复向量比例
- 输出 JSON 报告供后续对比
- `test/test_auto.py` 补充 embedding 质量检查步骤

## Capabilities

### New Capabilities

- `retrieval-diagnostic`: 检索管线分阶段诊断工具，定位问题发生在哪个环节

### Modified Capabilities

- `auto-test`: 端到端测试中新增向量质量检查（cosine_sim 分布、重复率）

## Impact

- `test/test_retrieval_diagnostic.py`：新增诊断脚本（基于 `debug_a1_trace.py` 的经验）
- `test/test_auto.py`：补充 embedding 质量断言
- `test/retrieval_diagnostic_schema.json`：JSON 报告格式定义（可选）

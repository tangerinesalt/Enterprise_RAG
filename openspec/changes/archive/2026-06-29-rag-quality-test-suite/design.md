## Context

已有 `test/debug_a1_trace.py` 完成了一次性诊断，但不可配置、不可重用、输出仅为控制台文本。需要将其转化为可配置、可重复、可比较的诊断工具。

## Goals / Non-Goals

**Goals:**
- 命令行可配置：知识库、查询、top_k、top_n、threshold
- 分阶段输出 embedding → vector retriever → BM25 → RRF → reranker 每阶段排名
- 自动诊断：cosine_sim 负数告警、阈值过滤率、重复向量比例
- JSON 报告输出，支持不同时间/配置的对比
- 集成到 `test/test_auto.py` 的端到端流程中

**Non-Goals:**
- 不修改检索管线本身（纯诊断工具）
- 不添加外部依赖
- 不做 UI 可视化（保留 CLI 输出）

## Decisions

### 1. 脚本结构：单一文件 + 可选的 schema 文件

`test/test_retrieval_diagnostic.py` 作为主入口，通过 argparse 接收参数。报告 schema 定义在脚本文档字符串中，不单独建文件。

### 2. 输出格式：终端表格 + JSON 文件

终端输出人类可读的分阶段排名表，同时输出 `test/diagnostic_output/<kb>_<timestamp>.json` 供 diff。

### 3. 诊断项

脚本自动检查以下异常：
- **E01**: cosine_sim 全为负数 → embedding 模型与查询不匹配
- **E02**: 阈值过滤率 > 50% → threshold 过高
- **E03**: ChromaDB 重复率 > 10% → 索引未幂等
- **E04**: A1 类片段（含查询关键词）排名低于中位数 → chunk 策略或 embedding 问题
- **E05**: Reranker 排名与 embedding 排名差异 > 50% → bi-encoder vs cross-encoder 严重分歧

### 4. auto-test 集成

`test_retrieval_diagnostic.py` 可被 `test_auto.py` 作为子进程调用，在端到端测试最后一步执行诊断并断言：无 E01、E03 告警。

## Risks / Trade-offs

- **[维护成本] 诊断脚本需要随检索管线演化** → 设计为模块化阶段函数，修改管线时只需更新对应阶段
- **[embedding 模型依赖] 诊断依赖 ollama embedding 服务在线** → 脚本启动时检查服务可用性，不可用时跳过 embedding 阶段

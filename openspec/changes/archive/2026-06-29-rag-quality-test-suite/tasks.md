## 1. 创建诊断脚本 `test_retrieval_diagnostic.py`

- [x] 1.1 实现命令行参数解析（kb_name, query, --top-k=12, --top-n=8, --threshold=0.2, --output-dir）
- [x] 1.2 实现 Stage 1：ChromaDB 全量查询 + cosine_sim 排名 + 重复检测
- [x] 1.3 实现 Stage 2：VectorIndexRetriever + 阈值过滤率计算
- [x] 1.4 实现 Stage 3：BM25 检索 + jieba 分词显示
- [x] 1.5 实现 Stage 4：RRF 融合 + 双路径来源标注（vec#X / bm25#X）
- [x] 1.6 实现 Stage 5：Reranker 最终评分 + 各阶段排名对比（embed# / rrf#）
- [x] 1.7 实现异常诊断引擎（E01:全负数, E02:高过滤率, E03:高重复率, E04:关键词排位低, E05:embed/rerank分歧）
- [x] 1.8 实现 JSON 报告输出（test/diagnostic_output/）

## 2. 集成到端到端测试

- [ ] 2.1 在 `test/test_auto.py` 中索引完成后调用诊断脚本作为子进程（待后续）
- [ ] 2.2 解析诊断输出中的 E01/E03 告警并打印 WARNING（待后续）

## 3. 验证

- [x] 3.1 运行 `python test/test_retrieval_diagnostic.py 062500 "A1是什么"` 确认输出完整
- [x] 3.2 运行 `python test/test_retrieval_diagnostic.py 062500 "金融风险管理" --top-k 8 --top-n 5 --threshold 0.3` 验证参数生效
- [ ] 3.3 运行 `python test/test_auto.py` 确认端到端测试通过（待后续）

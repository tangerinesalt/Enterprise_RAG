## 1. BM25 索引改为原始段落

- [ ] 1.1 在 `_build_bm25_retriever` 中，改为通过 KnowledgeBase 读取源文件目录，按 `\n\n` 分割段落构建 BM25 索引
- [ ] 1.2 保留 kb_name 级别的 BM25 缓存机制，段落级索引独立 cached
- [ ] 1.3 移除从 `index.docstore.docs` 提取 nodes 的旧逻辑

## 2. RRF 加权融合

- [ ] 2.1 修改 `_rrf_fusion` 参数：增加 `vector_weight=0.7, bm25_weight=0.3`
- [ ] 2.2 评分公式改为加权：`score += weight * 1/(k+rank+1)`

## 3. 纯向量模式

- [ ] 3.1 `build_retriever` 增加 `mode='hybrid'` 参数
- [ ] 3.2 `mode='vector-only'` 时跳过 BM25/RRF，直接返回阈值过滤后的 VectorIndexRetriever

## 4. 配置集成

- [ ] 4.1 `settings.json` 新增 `RETRIEVER_MODE` 配置项（默认 hybrid）
- [ ] 4.2 `config/settings.py` 读取 `RETRIEVER_MODE`
- [ ] 4.3 `build_retriever` 从 settings 读取默认 mode

## 5. 验证

- [ ] 5.1 运行诊断 `python test/test_retrieval_diagnostic.py 062500 "A1是什么"` 确认 RRF 不劣化
- [ ] 5.2 运行 `python test/test_retrieval_diagnostic.py 062500 "什么是数字化开户"` 确认 D2 正确命中
- [ ] 5.3 运行 `python test/test_retrieval_diagnostic.py 062500 "市场风险是什么"` 确认 A3 排名提升
- [ ] 5.4 测试 vector-only 模式下全部正常查询保持 #1

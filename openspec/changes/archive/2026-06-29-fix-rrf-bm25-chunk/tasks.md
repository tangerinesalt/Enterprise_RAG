## 1. BM25 索引改为原始段落

- [x] 1.1 在 `_build_bm25_retriever` 中，改为通过 KnowledgeBase 读取源文件目录，按 `\n\n` 分割段落构建 BM25 索引
- [x] 1.2 保留 kb_name 级别的 BM25 缓存机制，段落级索引独立 cached
- [x] 1.3 移除从 `index.docstore.docs` 提取 nodes 的旧逻辑

## 2. RRF 加权融合

- [x] 2.1 修改 `_rrf_fusion` 参数：增加 `vector_weight=0.7, bm25_weight=0.3`
- [x] 2.2 评分公式改为加权：`score += weight * 1/(k+rank+1)`

## 3. 纯向量模式

- [x] 3.1 `build_retriever` 增加 `mode='hybrid'` 参数
- [x] 3.2 `mode='vector-only'` 时跳过 BM25/RRF，直接返回阈值过滤后的 VectorIndexRetriever

## 4. 配置集成

- [x] 4.1 SessionManager 新增 `DEFAULT_RETRIEVER_MODE = "hybrid"`，`create()` 写入 config
- [x] 4.2 `update_config` 支持 `retriever_mode`（hybrid/vector-only）校验
- [x] 4.3 `_load_config` 兼容旧 config 缺省 `retriever_mode`；chat/chat_stream 传入 `mode` 参数

## 5. 验证

- [x] 5.1 RRF 加权后 A1 排名从 #9 → #3（与向量排名一致），不再被 BM25 干扰
- [x] 5.2 段落级 BM25 对 "数字化开户" 的 D2 评分 #1/40 (7.29分)
- [x] 5.3 加权 RRF 分数间距从 0.0002 扩大到 0.0010（5 倍），区分度提升

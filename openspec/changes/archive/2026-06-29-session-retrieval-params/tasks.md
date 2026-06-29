## 1. SessionManager Config 层扩展

- [x] 1.1 在 `SessionManager` 中添加类常量 `DEFAULT_TOP_K = 8`, `DEFAULT_TOP_N = 5`
- [x] 1.2 修改 `_load_config`：返回时确保 `top_k`/`top_n` 字段存在，缺失用默认值补全（不写回文件）
- [x] 1.3 修改 `create()`：`_save_config` 调用时传入 `top_k=8, top_n=5`
- [x] 1.4 修改 `info()`：返回数据中包含 `top_k`/`top_n` 值
- [x] 1.5 新增 `get_config(name)` 和 `update_config(name, **kwargs)` 方法，后者校验 `top_k >= 1` 且 `top_n >= 1`，校验通过后 `_save_config`

## 2. Retriever 模块参数化

- [x] 2.1 修改 `build_retriever` 签名：增加可选参数 `top_k: int = 5`
- [x] 2.2 将 `top_k` 传递给 `VectorIndexRetriever(similarity_top_k=top_k)` 和 `_build_bm25_retriever`
- [x] 2.3 修改 `_build_bm25_retriever`：接收 `top_k` 参数，传递给 `BM25Retriever(similarity_top_k=top_k)`
- [x] 2.4 修改 `_rrf_fusion`：`top_k` 参数不再硬编码 5，使用传入值

## 3. SessionManager 聊天流程串联参数

- [x] 3.1 修改 `chat()`：从 `config` 读取 `top_k`/`top_n`，传入 `build_retriever(index, kb_name, top_k=top_k)` 和 `SentenceTransformerRerank(top_n=top_n)`
- [x] 3.2 修改 `chat_stream()`：同上，将 config 中的参数应用到检索器和 reranker

## 4. CLI 新增 `session config` 子命令

- [x] 4.1 在 `app/modules/session/cli.py` 中新增 `cmd_config` 处理函数：展示当前参数，支持 `--set key=value` 修改
- [x] 4.2 在 parser 中注册 `config <name> [--set top_k=N] [--set top_n=N]` 子命令
- [x] 4.3 在 `app/cli.py` 的 epilog 和帮助文本中加入 `session config` 示例

## 5. REST API 新增配置端点

- [x] 5.1 在 `app/api/schemas.py` 中新增 `SessionConfigUpdateRequest`（`top_k: Optional[int]`, `top_n: Optional[int]`）
- [x] 5.2 在 `app/api/routers/session.py` 中新增 `PATCH /api/session/{name}/config` 路由
- [x] 5.3 修改 `GET /api/session/{name}` 的 info 响应包含 `top_k`/`top_n`
- [x] 5.4 验证错误值返回 400 且不修改数据

## 6. 前端：会话页添加参数编辑区域

- [x] 6.1 在 `api/index.ts` 中新增 `sessionApi.updateConfig(name, data)` 方法，调用 `PATCH /api/session/{name}/config`
- [x] 6.2 `SessionItem` 接口补充 `top_k: number` 和 `top_n: number` 字段
- [x] 6.3 在 `SessionChat.tsx` 左栏的 KB 绑定区域下方，新增「检索参数」区块：显示 `top_k` / `top_n` 为可编辑的数字输入框
- [x] 6.4 添加保存按钮：调用 `sessionApi.updateConfig()`，成功显示"已保存"提示，失败显示错误信息
- [x] 6.5 前端校验：`top_k >= 1` 且 `top_n >= 1`，不合法时阻止提交并提示

## Why

当前检索参数 `top_k`（向量/BM25 召回数）和 `top_n`（重排序保留数）在代码中硬编码（top_k=5, top_n=3），所有会话共用同一组参数。用户需要按会话粒度独立控制检索参数，并在会话运行时动态调整。

## What Changes

- 会话创建时在 `config.json` 中自动生成 `top_k`（默认 8）和 `top_n`（默认 5）字段
- CLI 新增 `session config` 子命令：展示当前参数，支持 `--set top_k=8 --set top_n=5` 修改
- REST API 新增 PATCH/PUT 路由修改会话参数，并在 `GET /session/{name}` 响应中包含参数
- 聊天核心流程从会话 `config.json` 读取 `top_k`/`top_n`，传递给 retriever 和 reranker，替代硬编码值
- 前端会话详情页展示参数，提供编辑功能

## Capabilities

### New Capabilities

- `session-retrieval-config`: 会话级检索参数持久化、读取、修改及在聊天中应用的能力

### Modified Capabilities

- `session-management`: config.json 新增 `top_k`/`top_n` 字段；create 时写入默认值；info/list 返回参数值
- `session-chat`: chat/chat_stream 从 config 读取 `top_k`/`top_n` 而非硬编码；影响检索 + 重排行为
- `api-session`: 新增修改参数的 API 端点；会话详情响应包含参数
- `ui-session-page`: 前端会话页展示并允许编辑参数（仅当前端已具备时）

## Impact

**后端 API**: 新增 `PUT /api/sessions/{name}/config`（或类似），接受 `{top_k: int, top_n: int}`  
**CLI**: 新增 `session config <name> [--set top_k=8] [--set top_n=5]`  
**SessionManager**: `_load_config`/`_save_config` 兼容旧 config（缺省时使用默认值）；`chat()` 和 `chat_stream()` 将参数下传到 retriever + reranker  
**Retriever**: `build_retriever` 新增 `top_k` 参数替代硬编码；`SentenceTransformerRerank` 的 `top_n` 从 config 传入

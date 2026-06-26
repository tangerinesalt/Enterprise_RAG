## Why

当前 RAG 聊天体验有三个明显的短板：(1) 聊天请求必须等 LLM 完整生成后才返回，长回答前端空白十几秒；(2) LLM 回复中的 Markdown 格式（代码块、列表、标题）渲染为纯文本，可读性差；(3) 首次聊天的 `init_models()` 阻塞耗时约 0.5s，让第一个请求慢于后续。这三个问题都不涉及架构改动，修复成本低，但对用户体验提升显著。

## What Changes

- **流式聊天**：后端 `/api/session/chat` 改为 SSE (Server-Sent Events) 响应，逐 token 推送；前端使用 EventSource / ReadableStream 实时渲染，配合打字机效果。
- **Markdown 渲染**：前端聊天消息组件支持 Markdown（代码语法高亮、表格、列表、链接），LLM 回复不再以纯文本显示。
- **模型预热**：FastAPI 启动时通过 `lifespan` event 提前调用 `init_models()`，消除首次聊天的模型初始化延迟。保留线程锁防重复的兜底。
- 后端新增 SSE 依赖 `sse-starlette`；前端新增 `react-markdown` + `remark-gfm` + `react-syntax-highlighter` 依赖。

## Capabilities

### New Capabilities
- `streaming-chat-response`: 基于 SSE 的流式聊天响应，后端逐 token 推送，前端逐 token 渲染
- `markdown-message-render`: 前端聊天消息的 Markdown 渲染，含代码语法高亮
- `model-startup-warmup`: 服务器启动时预先初始化 LLM + Embedding 模型，消除首次请求开销

### Modified Capabilities
- `session-chat`: 聊天核心逻辑新增流式生成模式，兼容非流式回退
- `api-session`: 新增流式聊天端点；聊天请求 Schema 添加 `stream` 参数
- `ui-session-page`: 聊天消息显示区域支持 Markdown 渲染；新增流式响应的打字机效果

## Impact

- **后端**：`app/api/routers/session.py` 新增流式端点；`app/modules/session/session_manager.py` 新增流式生成方法；`app/api/server.py` 添加 lifespan 事件；`app/api/schemas.py` 扩展请求模型。
- **前端**：`ui/src/pages/SessionChat.tsx` 重写消息渲染和请求逻辑；`ui/package.json` 新增依赖。
- **API**：新增 `POST /api/session/chat/stream` 端点，响应 `text/event-stream`。
- **依赖**：后端新增 `sse-starlette`；前端新增 `react-markdown` + `remark-gfm` + `react-syntax-highlighter`。
- **无破坏性变更**：现有同步聊天端点保持兼容，流式为新端点。

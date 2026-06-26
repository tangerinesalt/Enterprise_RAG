## 1. 模型预热 (model-startup-warmup)

- [x] 1.1 修改 `app/api/server.py`：添加 FastAPI `lifespan` context manager，在 startup 时调用 `init_models()`，打印 `[TIMING]` 日志
- [x] 1.2 验证：启动 server 后立即调用 `/api/health`，控制台应有模型初始化的 timing 日志；第一次 chat 请求不再有 `init` 延迟

## 2. 后端流式聊天端点 (streaming-chat-response — backend)

- [x] 2.1 在 `app/modules/session/session_manager.py` 中新增 `chat_stream()` generator 方法：
  - 复用现有 retrieve + LLM streaming query engine (`streaming=True`)
  - 逐 token yield
  - 收集 buffer → 流结束后 persist + yield sources + done
- [x] 2.2 在 `app/api/schemas.py` 中新增 `SessionChatStreamRequest`（可选，可与现有 `SessionChatRequest` 复用）
- [x] 2.3 在 `app/api/routers/session.py` 中新增 `POST /api/session/chat/stream` 路由：
  - 返回 `StreamingResponse(generate(), media_type="text/event-stream")`
  - SSE 事件格式：`start`, `token`, `sources`, `done`, `error`
  - 异常处理：catch `SessionError` 等 → 发送 `error` SSE 事件
- [x] 2.4 验证：用 `curl` 测试流式端点，确认逐 token 推送

## 3. 前端流式消费 (streaming-chat-response — frontend)

- [x] 3.1 在 `ui/src/api/index.ts` 中新增 `sessionApi.chatStream()` 方法：
  - 使用 `fetch` + `ReadableStream`（POST 方法，JSON body）
  - 逐 chunk 解析 SSE 事件
  - 返回事件回调或 async generator
- [x] 3.2 修改 `ui/src/pages/SessionChat.tsx`：
  - 发送消息时调用流式 API
  - 收到 `token` 事件 → 增量追加到当前 assistant 消息（打字机效果）
  - 收到 `sources` 事件 → 显示折叠的来源列表
  - 收到 `done` 事件 → 刷新聊天列表
  - 收到 `error` 事件 → 显示错误提示
  - 支持按 Enter 发送（当前已实现，保持兼容）
  - 流式期间禁用发送按钮
- [x] 3.3 验证：打开 UI，发送消息，确认打字机效果工作

## 4. Markdown 渲染 (markdown-message-render)

- [x] 4.1 安装前端依赖：`npm install react-markdown remark-gfm react-syntax-highlighter @types/react-syntax-highlighter`
- [x] 4.2 创建 `ui/src/components/MarkdownMessage.tsx` 组件：
  - 使用 `react-markdown` + `remark-gfm`
  - 代码块使用 `react-syntax-highlighter` + Prism 主题（只导入常用语言：python, javascript, bash, json, sql, yaml）
  - 添加复制的按钮（Clipboard API）
  - 使用 `rehype-sanitize` 防止 XSS
- [x] 4.3 修改 `ui/src/pages/SessionChat.tsx`：将 assistant 消息的渲染从 `<div>{msg.content}</div>` 改为 `<MarkdownMessage content={msg.content} />`
- [x] 4.4 验证：发送一个会返回代码块的查询，确认语法高亮和格式化正常

## 5. 验证与修复

- [x] 5.1 验证所有场景：流式聊天 + 同步聊天 + Markdown 渲染 + 模型预热
- [x] 5.2 检查现有功能未受影响：KB 管理页面、Session 列表页面、CLI 命令

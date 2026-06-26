## Context

RAG V 目前使用同步 REST API 处理聊天请求：客户端 POST `/api/session/chat`，服务端完成检索 → LLM 生成 → 持久化全流程后一次性返回 JSON。对于长回答，客户端等待期间无任何反馈。此外，LLM 回复为 Markdown 格式但前端以纯文本渲染，首次聊天有 `init_models()` 预热延迟。

三个问题各自独立但都围绕聊天体验，适合在同一 change 内解决。

```
Current (sync):
  Client ─POST /chat─→ 等待检索+生成+持久化 ─完整JSON─→ Client

Target (streaming):
  Client ─POST /chat/stream─→ 
         ← token 1 ──
         ← token 2 ──
         ← ...      ──  SSE 流
         ← sources  ──
         ← done     ──
```

## Goals / Non-Goals

**Goals:**
- 新增流式聊天端点，逐 token 推送 LLM 生成结果到前端
- 前端聊天消息支持完整 Markdown 渲染（含代码语法高亮）
- FastAPI 启动时预热模型，消除首次聊天初始化延迟
- 现有同步端点保持兼容，不做破坏性变更

**Non-Goals:**
- 不修改 CLI 的聊天行为（CLI 继续使用同步方式）
- 不引入 WebSocket（SSE 足够且实现更轻量）
- 不考虑多模态响应（纯文本 Markdown 即可）
- 不涉及聊天历史编辑或删除单条消息

## Decisions

### 1. SSE 优于 WebSocket

| 维度 | SSE | WebSocket |
|------|-----|-----------|
| 协议 | HTTP 长连接 | 独立协议 |
| 方向 | 服务端→客户端单向 | 双向 |
| 实现 | `StreamingResponse` + generator | `WebSocketEndpoint` |
| 浏览器支持 | EventSource API | WebSocket API |
| 复杂度 | 低 | 中 |

SSE 完美匹配"服务端逐 token 推送给客户端"的单向场景，实现简单，无需额外依赖。FastAPI 原生支持 `StreamingResponse`。

### 2. 新增端点而非修改现有端点

创建 `POST /api/session/chat/stream` 而非在 `/chat` 上加 `?stream=true` 参数。原因：
- 路由逻辑差异大（同步 vs generator），拆分维护更清晰
- OpenAPI schema 自动区分两种响应类型（JSON vs text/event-stream）
- 客户端可自由选择同步或流式方式

### 3. 同步 generator + thread pool

`SessionManager` 当前的聊天流程（`index.as_query_engine(streaming=True).query()` → `.response_gen`）是同步的。直接传递给 FastAPI 的 `StreamingResponse`，后者自动在 thread pool 中运行 sync generator，不阻塞 event loop。

如果用纯 async path（`aquery()`），需要改写 `SessionManager` 的链路为 async，影响范围大。权衡后选择 sync generator + `StreamingResponse` 的组合。

### 4. 持久化时机：流结束后

SSE 事件顺序：
```
event: start   → {"chat_file": "xxx"}
event: token   → {"token": "逐 token..."}
event: token   → {"token": "..."}  
event: sources → {"sources": [...]}
event: done    → {"chat_file": "xxx"}
```

将所有 token 收集到 buffer，流结束后执行 persist + 发送 sources/done。这样客户端先看到完整打字机效果，最后收到来源信息。

### 5. models 预热：lifespan event

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    from config.init import init_models
    init_models()  # warm up
    yield
```

利用 FastAPI 的 `lifespan` 机制（替代已废弃的 `on_event`），在 worker 启动后、接受请求前执行。`init_models()` 本身有线程锁防止重复初始化，安全无副作用。

### 6. 前端流式接收：fetch + ReadableStream

EventSource API 方便但只支持 GET 请求。聊天是 POST（请求体含 query/chat_file），所以使用 `fetch + ReadableStream` 读取 SSE。配合 `useEffect` 逐 token 追加到消息列表，产生打字机效果。

```typescript
const response = await fetch('/api/session/chat/stream', { method: 'POST', body: ... });
const reader = response.body!.getReader();
// 逐 chunk 解析 SSE, 逐 token setState
```

## Data Flow

```
                    ┌──────────────────────────────┐
                    │   init_models() warm start   │
                    │   (lifespan startup)          │
                    └──────────┬───────────────────┘
                               │
  Client ─POST /chat/stream───▼─────────────────────────┐
         │  1. 解析请求，确定 chat_file                  │
         │  2. 追加用户消息到 SimpleChatStore            │
         │  3. ChromaDB 检索 (similarity_top_k=5)       │
         │  4. LLM streaming query engine               │
         │     ┌─ 逐 token: yield token SSE event ──→  │
         │     └─ 收集到 buffer                         │
         │  5. 完整回答 → 追加到 SimpleChatStore        │
         │  6. persist to disk                          │
         │  7. yield sources SSE event                  │
         │  8. yield done SSE event                     │
         └──────────────────────────────────────────────┘
```

## Risks / Trade-offs

- **[Risk] 客户端断开连接后，后端 generator 继续运行**：`StreamingResponse` 在客户端断开后会抛出 `StopAsyncIteration` 并终止 generator。但若 generator 在 persist 步骤才失败，可能产生已流式但未持久化的回答。→ 可接受：下次用户刷新会重新提问。
- **[Risk] `react-markdown` 包体积**：`react-markdown` + `react-syntax-highlighter` 合计约 ~150KB gzipped（含 Prism 语言包）。→ 可接受，对 SPA 总包体积影响有限。
- **[Trade-off] Sync generator 在 thread pool 中运行**：每个流式聊天请求占用一个 thread pool worker，高并发下可能耗尽线程。→ 当前 MVP 阶段可接受（预期并发 < 10）。未来可迁移到纯 async path。
- **[Risk] 代码高亮语言包过大**：`react-syntax-highlighter` 默认包含所有语言。→ 按需导入常见语言（Python, JavaScript, Bash, JSON, SQL, YAML, Markdown）。

## Open Questions

- 是否需要在 SSE 事件中添加 `event_id` 以支持断线重连后从断点恢复？→ 当前不实现，第一次迭代不做重连。

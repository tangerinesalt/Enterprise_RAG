## Why

流式聊天（`improve-chat-ux`）的 `chat_stream()` 方法在持久化时只保存了回答文本，来源信息仅通过 SSE 事件发送到前端 React state。用户切换聊天后重新加载消息时，API 返回的 `{role, content}` 不包含 `sources` 字段，前端折叠的「📎 来源」按钮消失。同步聊天（`chat()`）无此问题，因为来源文本被直接追加到了消息 content 中。

## What Changes

- **后端 `chat_stream()` 持久化**：将来源信息存入 `ChatMessage.additional_kwargs`，而不是只存 answer 文本。
- **后端 `get_messages()` API 返回来源**：`GET /api/session/{name}/chats/{chat_file}` 返回的消息对象新增 `sources` 字段，从 `additional_kwargs` 中提取。
- **前端消息加载保留 sources**：`useEffect` 加载消息时保留 API 返回的 `sources` 字段，折叠按钮在切换聊天后仍然存在。
- 向后兼容：旧聊天文件（来源存于 content 文本中）不受影响。

## Capabilities

### New Capabilities
- `chat-source-persistence`: 流式聊天来源信息的持久化与 API 透传

### Modified Capabilities
- `streaming-chat-response`: 持久化阶段额外保存 sources 到 additional_kwargs
- `api-session`: 聊天消息 API 返回新增 `sources` 字段
- `ui-session-page`: 消息加载时保留 sources 状态

## Impact

- **后端**：`app/modules/session/session_manager.py` 的 `chat_stream()` 和 `get_messages()` 修改。
- **API**：`GET /api/session/{name}/chats/{chat_file}` 响应体新增字段（向后兼容）。
- **前端**：`ui/src/pages/SessionChat.tsx` 的消息加载逻辑适配。
- **无依赖变更**。

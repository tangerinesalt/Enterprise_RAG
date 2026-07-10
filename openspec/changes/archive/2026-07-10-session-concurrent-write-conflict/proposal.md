## Why

两个浏览器页面同时向同一个 session 发消息时，`_session_config_lock` 序列化 `_ensure_chat_target` 调用，后一个请求的 `_save_config` 覆盖前一个的 `active_chat`。此外，页面级别的 `activeChat` 状态互相独立，前端无法感知另一个页面切换了聊天，导致两个请求的 LLM 响应可能写入同一个聊天文件或丢失。

## What Changes

- **`_ensure_chat_target` 只读不写**：将 `active_chat` 写入操作从 `_ensure_chat_target` 中剥离，只有前端主动 `select_chat` 时才修改 `active_chat`
- **`chat_stream` 按 chat_file 隔离**：后端将 `active_chat` 的写入移到 `chat_stream` 之外，确保流式请求不依赖 `active_chat` 配置
- **前端 `chatStream` 始终传递 chat_file**：确保每个请求都明确指定目标聊天文件，不依赖后端的 `active_chat` 默认值

## Capabilities

### New Capabilities

N/A

### Modified Capabilities

- `session-chat-concurrency`: 更新并发流式请求时的配置隔离机制

## Impact

- **后端**：`app/modules/session/session_manager.py` — `_ensure_chat_target` 行为调整、`chat_stream` 参数处理
- **前端**：`ui/src/pages/SessionChat.tsx` — 调用 `chatStream` 时始终显式传递 `chat_file`

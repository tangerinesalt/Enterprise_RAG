## Why

当用户在一个聊天（Chat A）中发起对话、助手流式回复未完成时切换到其他聊天，Chat A 的流式生成器被客户端 abort 强制终止。此时后端 LLM 的 `response.response_gen`（生成器）未被正确关闭，Chat A 的 chat store 中残留了一条没有对应助手回复的用户消息。之后用户重新回到 Chat A 发起了第二次对话（成功完成），但再次点击 Chat A 时后端彻底卡死，所有 API 请求无法响应。

## What Changes

### 后端核心修复

- **`chat_stream()` 中 `except Exception` 改为 `except BaseException`**：捕获 `GeneratorExit`（客户端断开连接时 FastAPI 向生成器注入该异常），确保 LLM 的 `response.response_gen` 被及时关闭，并清理 chat store 中已写入的用户消息
- **`generate()` 路由层增加客户端断开检测**：在 `StreamingResponse` 的 generator 中监听 `request.is_disconnected`，主动退出生成

### 状态一致性修复

- **`_prepare_chat_turn()` 回滚机制**：如果 `chat_stream()` 因客户端断开异常退出，需撤销该次 `_prepare_chat_turn()` 已持久化的用户消息，避免 chat store 中残留孤立用户消息
- **静态聊天文件状态检测**：`get_messages()` 加载 store 后检测是否存在孤立消息（user 后无 assistant），若存在则自动清除

### 非目标

- 不改变前端行为（前端已经正确 abort fetch）
- 不改动 LlamaIndex 的 SimpleChatStore 实现

## Capabilities

### New Capabilities

- `chat-stream-graceful-shutdown`: 流式聊天连接断开时的优雅关闭和状态回滚机制

### Modified Capabilities

- `session-chat-concurrency`: 更新流式聊天并发和中断时的后端一致性保证

## Impact

- **后端**：`app/modules/session/session_manager.py` — `chat_stream()` 异常处理层次修改、状态回滚逻辑、孤立消息检测
- **前端**：`ui/src/pages/SessionChat.tsx` — 可选改进：切换聊天时等待后端确认上次流已终止再切换

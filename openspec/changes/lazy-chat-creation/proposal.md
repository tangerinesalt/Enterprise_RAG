## Why

当前会话聊天页面的行为有两个问题：

1. **进入会话时自动加载了一个旧聊天** — 用户只是想看看会话配置或开始新问答，却被迫看到最早的聊天内容（`chats[0]`），需要手动点"新聊天"才能清空。
2. **"新聊天"按钮立即写磁盘** — 点击后马上创建空 JSON 文件，即使最终没有发送任何消息，也会产生孤立文件。

改为「按需创建」后，用户打开会话和点击新聊天都看到空白状态，第一次提交问答时才生成聊天文件，更符合直觉也减少了 I/O。

## What Changes

- `SessionChat.tsx`：进入会话时 `activeChat` 初始为 `null`，不自动选中任何聊天文件
- `SessionChat.tsx`：点击"新聊天"仅清空消息区、将 `activeChat` 置为 `null`，不调用 API
- `SessionChat.tsx`：用户提交问题时，若 `activeChat` 为 `null`，则先调用 `newChat` API 创建文件再发送
- `session_manager.py`：`chat_stream()` 和 `chat()` 中 "无 chat_file 时自动新建" 的行为不变，作为后端兜底
- 后端不修改 — 「按需创建」的逻辑完全由前端控制

## Capabilities

### New Capabilities
- `lazy-chat-ui`: 前端的按需聊天创建行为，包括空白初始状态和新聊天逻辑

### Modified Capabilities
- `session-chat`: 修改用户进入会话时的初始视图行为，不再自动加载聊天记录

## Impact

| 范围 | 影响 |
|------|------|
| `ui/src/pages/SessionChat.tsx` | 修改 3 个 useEffect + handleNewChat + handleSubmit |
| `app/modules/session/session_manager.py` | 无需修改（后端已支持 chat_file 为 null） |
| API 契约 | 无变化 |
| 用户体验 | 进入会话不再自动加载旧聊天，新聊天不再预创建文件 |

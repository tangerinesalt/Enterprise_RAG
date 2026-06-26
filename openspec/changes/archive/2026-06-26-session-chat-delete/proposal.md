## Why

当前 UI 的会话聊天页面（`SessionChat.tsx`）左侧聊天列表中，每条聊天记录没有删除功能。后端 `SessionManager.delete()` 已支持按 `chat_file` 删除单条聊天，但缺少 API 路由和前端 UI 入口。

## What Changes

- **API 新增**：`DELETE /api/session/{name}/chats/{chat_file}` 路由，调用 `_session.delete(name, chat_file)`
- **UI 新增**：会话聊天页面的左侧聊天列表，每条聊天记录右侧添加删除按钮（🗑️），点击后确认删除并刷新列表
- 删除后自动切换到其他可用聊天，若没有聊天则显示空状态

## Capabilities

### New Capabilities
- `chat-delete`: 单条聊天的删除功能（API + UI）

### Modified Capabilities
- `api-session`: 新增删除聊天端点
- `ui-session-page`: 聊天列表增加删除操作

## Impact

- **后端**：`app/api/routers/session.py` 新增 `DELETE /{name}/chats/{chat_file}` 路由
- **前端**：`ui/src/api/index.ts` 新增 `deleteChat()` 方法；`ui/src/pages/SessionChat.tsx` 聊天列表每项增加删除按钮
- **无破坏性变更**

## Context

`SessionManager.delete(name, chat_file)` 已支持单条聊天删除。只需补 API 路由和前端入口。

## Goals / Non-Goals

**Goals:**
- `DELETE /api/session/{name}/chats/{chat_file}` 端点
- 前端聊天列表每条右侧加删除按钮
- 删除后自动切换到其他聊天或显示空状态

**Non-Goals:**
- 不修改后端 `SessionManager.delete()` 逻辑
- 不添加批量删除

## Decisions

### API 设计
```
DELETE /api/session/{name}/chats/{chat_file}
→ {"ok": true, "data": {"name": "...", "chat_file": "..."}}
```

复用 `_session.delete(name, chat_file)`。

### 前端行为
- 删除后：如果 `activeChat` 正好是被删的，切到列表第一条聊天（若有）；若无聊天则清空
- 确认弹窗用 `confirm()`，与现有删除风格一致

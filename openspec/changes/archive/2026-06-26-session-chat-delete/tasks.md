## 1. 后端 API

- [x] 1.1 在 `app/api/routers/session.py` 中新增 `DELETE /{name}/chats/{chat_file}` 路由
- [x] 1.2 验证：用 curl 测试删除聊天 API

## 2. 前端

- [x] 2.1 在 `ui/src/api/index.ts` 中新增 `deleteChat(name, chatFile)` 方法
- [x] 2.2 在 `ui/src/pages/SessionChat.tsx` 的聊天列表每项右侧添加 🗑️ 按钮
- [x] 2.3 实现删除逻辑：confirm → 调用 API → 刷新列表 → 切换 activeChat

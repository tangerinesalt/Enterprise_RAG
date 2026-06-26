## 1. 后端持久化

- [x] 1.1 修改 `app/modules/session/session_manager.py` 的 `chat_stream()`：在 persist 时将 `sources` 存入 `ChatMessage.additional_kwargs`
- [x] 1.2 验证：启动服务，发送流式聊天请求，检查 `sessions/<name>/chats/<file>.json` 中 assistant 消息的 `additional_kwargs.sources` 存在

## 2. 前端加载 sources

- [x] 2.1 修改 `ui/src/pages/SessionChat.tsx` 的 `useEffect` 消息加载：从 `d.messages` 提取 `additional_kwargs?.sources` 映射到 `msg.sources`
- [x] 2.2 验证：打开 UI，发送消息等待回答，切换聊天再切回，确认折叠按钮「📎 来源」仍然存在

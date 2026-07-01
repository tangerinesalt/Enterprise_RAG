## 1. 删除自动选中逻辑

- [ ] 1.1 移除 `SessionChat.tsx` 中第 44-49 行的 `useEffect`，该 effect 在 `activeChat` 为 null 时自动选 `chats[0]`
- [ ] 1.2 确认 `load()` 中 `sessionApi.listChats()` 仍然调用，侧边栏聊天列表正常显示

## 2. 新聊天改为纯前端操作

- [ ] 2.1 修改 `handleNewChat`：`setActiveChat(null)` + `setMessages([])`，去掉 `sessionApi.newChat()` 调用
- [ ] 2.2 确认"新聊天"后 UI 显示空状态提示，而非空白消息区

## 3. 提交时按需创建

- [ ] 3.1 在 `handleSubmit` 中，`chatStream` 调用前增加判断：若 `activeChat` 为 null，先 `await sessionApi.newChat(name)`，用返回的 `chat_file` 作为流式请求参数
- [ ] 3.2 确认 `onDone` 回调中 `setActiveChat(chat_file)` 正确更新状态，使提交后页面切换到新聊天

## 4. 验证

- [ ] 4.1 进入有聊天的会话 → 显示空白状态，侧边栏有聊天列表
- [ ] 4.2 点击已有聊天 → 加载该聊天的历史消息
- [ ] 4.3 点击新聊天 → 空白状态，网络面板无 `POST /api/session/new`
- [ ] 4.4 在空白状态下提交问题 → 自动创建聊天文件，消息正常显示
- [ ] 4.5 在有聊天文件时提交 → 追加到该聊天，不重复创建
- [ ] 4.6 前端 TypeScript 编译通过（`npm run build`）

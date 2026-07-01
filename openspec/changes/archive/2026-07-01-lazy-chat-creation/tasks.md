## 1. 删除自动选中逻辑

- [x] 1.1 移除 `SessionChat.tsx` 中第 44-49 行的 `useEffect`，该 effect 在 `activeChat` 为 null 时自动选 `chats[0]`
- [x] 1.2 确认 `load()` 中 `sessionApi.listChats()` 仍然调用，侧边栏聊天列表正常显示

## 2. 新聊天改为纯前端操作

- [x] 2.1 修改 `handleNewChat`：`setActiveChat(null)` + `setMessages([])`，去掉 `sessionApi.newChat()` 调用
- [x] 2.2 确认"新聊天"后 UI 显示空状态提示，而非空白消息区

## 3. 提交时按需创建

- [x] 3.1 在 `handleSubmit` 中，`chatStream` 调用前增加判断：若 `activeChat` 为 null，先 `await sessionApi.newChat(name)`，用返回的 `chat_file` 作为流式请求参数
- [x] 3.2 `onDone` 回调使用局部变量 `chatFile` 而非闭包中的 `activeChat`，避免 stale closure

## 4. 聊天预览元数据

- [x] 4.1 `_gen_chat_filename` 保持当前时间戳命名（无需修改）
- [x] 4.2 `chat_stream()` 和 `chat()` 完成首次写入后，将 query 前 15 字存入 `config.json` 的 `chat_previews` 映射
- [x] 4.3 `list_chats()` 从 `config.json` 读取 `chat_previews`，返回 `preview` 字段
- [x] 4.4 前端侧边栏显示 `c.preview || c.file`
- [x] 4.5 向后兼容：`previews.get(f)` 返回 undefined 时前端 fallback 到 `c.file`

## 5. 验证

- [x] 5.1 进入有聊天的会话 → 显示空白状态，侧边栏有聊天列表（API `GET /api/session` 无文件打开）
- [x] 5.2 点击已有聊天 → 加载该聊天的历史消息（`setActiveChat` 切换正常）
- [x] 5.3 点击新聊天 → 空白状态，`handleNewChat` 仅为 `setActiveChat(null)` 纯前端操作
- [x] 5.4 在空白状态下提交问题 → `newChat` API 创建文件，chat_stream 正常，preview 已保存
- [x] 5.5 在有聊天文件时提交 → `activeChat` 非 null，跳过 `newChat`，追加到当前聊天
- [x] 5.6 旧聊天文件在侧边栏显示文件名（`preview` 为 undefined 时 fallback 到 `c.file`）
- [x] 5.7 前端 TypeScript 编译通过（`tsc -b --noEmit` → 0 errors）

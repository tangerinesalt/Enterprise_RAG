## Context

当前 `SessionChat.tsx` 的状态管理：

```
进入会话 → load() 获取 chats → useEffect 自动选 chats[0] → 加载该聊天的消息
点击新聊天 → newChat API → activeChat=新文件 → 空消息区
提交问题 → chatStream(name, query, activeChat) → 追加到当前聊天
```

改为：

```
进入会话 → load() 获取 chats → activeChat=null → 空白状态
点击新聊天 → activeChat=null, messages=[] → 空白状态（无 API 调用）
提交问题 → 若 activeChat=null 则先 newChat → chatStream → onDone 设置 activeChat
点击已有聊天 → getMessages → 加载历史
```

## Goals / Non-Goals

**Goals:**

- 进入会话时显示空白聊天区域，不自动加载任何聊天记录
- 点击"新聊天"仅在前端清空状态，不写磁盘
- 第一次提交问题时自动创建聊天文件

**Non-Goals:**

- 不修改后端逻辑（后端已支持 `chat_file=None` 时自动新建）
- 不修改 API 契约
- 不修改 CLI 行为（CLI 的按需创建逻辑不变）
- 不修改聊天列表侧边栏的展示逻辑

## Decisions

### Decision 1: 用 `activeChat === null` 表示"空白状态"

无需引入额外 flag。现有 JSX 已有分支：

```
{activeChat ? (聊天区域) : (空状态提示)}
```

进入会话和点击新聊天都设为 `null` 即可。

### Decision 2: 提交时按需创建

`handleSubmit` 中增加前置逻辑：

```
handleSubmit:
  if (!activeChat)
    res = await sessionApi.newChat(name)
    activeChat = res.chat_file        ← 局部变量
  chatStream(name, query, activeChat)
```

`chatStream` 的 `chat_file` 参数直接传 `activeChat`（无论是 null 创建后还是已有）。

### Decision 3: onDone 中设置 activeChat

`onDone` 回调在流结束后设置 `setActiveChat(chat_file)`，确保提交后状态切换到新建/当前聊天。

### Decision 4: 删除自动选中 useEffect

移除第 44-49 行的 `useEffect`，只保留 `load()` 中的 `sessionApi.listChats()` 用于填充侧边栏。

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| 用户提交前点了已有聊天，空白状态的消息未保存 | 提交按钮已有 `loading` guard；且在 `activeChat` 为 null 时进入 submit 前没有消息可丢 |
| `onDone` 中 `activeChat` 闭包过期 | 提交前用局部变量捕获 `chat_file`，而不是依赖 state |
| StrictMode 导致 `newChat` 被调两次 | 后端 `_gen_chat_filename` 有冲突处理，第二次会生成 `_1.json`；但前端应避免 — 在 `loading` 状态下禁用提交按钮（已有） |

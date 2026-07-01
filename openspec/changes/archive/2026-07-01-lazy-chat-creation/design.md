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

## State Transitions

```
                         ┌─────────────────────┐
                         │  空白状态             │
                         │  activeChat = null   │
                         │  messages = []       │
                         └──────┬──────────────┘
                    ┌───────────┼───────────┐
                    ▼           ▼           │
            点击已有聊天    直接提交问题       │
                    │           │            │
                    ▼           ▼            │
          ┌──────────────┐  ┌──────────┐     │
          │ 已有聊天视图   │  │ 创建新聊天 │     │
          │ activeChat=X  │  │ newChat() │     │
          │ messages 加载  │  │ 然后提交   │     │
          └──────┬───────┘  └─────┬────┘     │
                 │                │          │
                 ▼                ▼          │
             提交问题 ──────→ chatStream()    │
                                │            │
                                ▼            │
                          ┌──────────┐       │
                          │ onDone   │       │
                          │ 回到视图  │───────┘
                          └──────────┘
```

关键规则：
- **点击侧边栏聊天** → `setActiveChat(c.file)`，`activeChat` 不再是 null
- **提交时 `activeChat` 不为 null** → 追加到该聊天，不会创建新文件
- **提交时 `activeChat` 为 null** → 先 `newChat` 再提交

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

### Decision 5: 聊天预览用元数据而非文件名

不在文件名中加入 query 预览（避免编码问题、不与 `_gen_chat_filename` 的时间戳逻辑耦合）。改为：

- `_gen_chat_filename` 保持当前时间戳命名：`2026_07_01_11_58.json`
- `chat_stream()` 完成首次写入后，在 `SimpleChatStore` 的 `additional_kwargs` 中记录 `first_query_preview`
- 在会话配置 `config.json` 中增加 `chat_previews` 映射：`{"2026_07_01_11_58.json": "数字化转型..."}`
- `list_chats()` 返回 `preview` 字段（文件名中的 query 前 10 字 + "..."）
- 前端侧边栏显示 `c.preview || c.file`

存储位置选 `config.json` 而非单独文件，因为：
1. 已经是一个轻量 JSON，不需要额外文件打开
2. 只写一次（首次提交时），后续读 `list_chats()` 时直接从配置取
3. 向后兼容：旧聊天没有 preview 则 fallback 到文件名

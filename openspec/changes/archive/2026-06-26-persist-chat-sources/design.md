## Context

`chat_stream()` 在 `improve-chat-ux` 中实现，目前持久化时只存 `content`（纯回答），来源通过 SSE 推送到前端 React state。切换聊天时 `useEffect` 重新调用 `getMessages` API，返回的 `{role, content}` 不含 `sources`，React state 被覆盖，折叠按钮消失。

同步 `chat()` 则把来源文本追加入 `content`，切换聊天后信息不丢——但缺点是 sources 混在文本中，前端无法做折叠交互。

方案 B 的目标是：sources 结构化储存和返回，前端折叠按钮在切换后仍然可用。

```
方案 A（简化版）:                            方案 B（本 change）:
chat_stream() 持久化                          chat_stream() 持久化
  content = answer                              content = answer
  + "\n\n---\n来源:\n..."                +   additional_kwargs = {"sources": [...]}
                                                │
重新加载 → 来源文本可见                          重新加载 → 折叠按钮仍可工作
但折叠按钮不可展开                               且来源结构化可操作
```

## Goals / Non-Goals

**Goals:**
- `chat_stream()` 持久化时将 sources 存入 `ChatMessage.additional_kwargs`
- `get_messages()` 返回的消息中附带 `sources` 字段
- 前端 `useEffect` 加载消息时识别 API 返回的 `sources`，折叠按钮在切换后保留
- 旧聊天文件（sources 在 content 文本中）不受影响

**Non-Goals:**
- 不修改 `chat()` 同步路径（它已通过 content 文本保存来源，足够用）
- 不引入数据库迁移（SimpleChatStore 的 JSON 格式自动兼容新增字段）

## Decisions

### 1. 使用 `additional_kwargs` 而非独立存储

`SimpleChatStore` 的 `ChatMessage` 原生支持 `additional_kwargs: dict`，LlamaIndex 将其序列化为 JSON 字段。不需要改 schema、不需要迁移、零成本。

```python
store.add_message(name, ChatMessage(
    role=MessageRole.ASSISTANT,
    content=answer,
    additional_kwargs={"sources": sources},
))
```

### 2. `get_messages()` 提取 sources 返回

当前 `get_messages()` 已返回 `additional_kwargs`（见 session_manager.py 第 206 行）。但前端 API 类型定义和消息接口都未利用这个字段。

只需在前端解析层提取 `additional_kwargs.sources` 映射到 `msg.sources`。

### 3. 前端 `useEffect` 解析 sources

当前 `useEffect` 直接 `setMessages(d.messages)`，而 `d.messages` 是 `{role, content, additional_kwargs}[]`。需要在 set 之前做一次映射：

```typescript
.then(d => setMessages(d.messages.map(m => ({
  role: m.role,
  content: m.content,
  sources: m.additional_kwargs?.sources,
}))))
```

这样 `msg.sources` 在有值的消息上自动填充，折叠按钮自然显示。

## Data Flow

```
chat_stream() persist:
  SimpleChatStore → {"role": "assistant",
                     "content": "硅是主要材料...",
                     "additional_kwargs": {"sources": [
                       {"text": "...", "score": 0.92},
                       ...
                     ]}}

get_messages() API:
  GET /api/session/{name}/chats/{chat_file}
  → {"ok": true, "data": {"messages": [
       {"role": "assistant",
        "content": "硅是主要材料...",
        "additional_kwargs": {"sources": [...]}}
     ]}}

Frontend useEffect:
  d.messages.map(m => ({
    role: m.role,
    content: m.content,
    sources: m.additional_kwargs?.sources,  ← 新增
  }))
  → msg.sources 有值 → 折叠按钮 ✅
```

## Risks / Trade-offs

- **[Risk] 旧聊天文件无 sources 字段**：`additional_kwargs` 为 `{}` 或 `None`，前端 `?.` 安全访问，折叠按钮不显示，content 文本中的来源信息仍然可见。无破坏性。
- **[Risk] sources 数据体积**：每次回答附带最多 5 条来源片段（各 ~300 字符），约 2KB/条消息。对 SimpleChatStore JSON 而言可忽略。

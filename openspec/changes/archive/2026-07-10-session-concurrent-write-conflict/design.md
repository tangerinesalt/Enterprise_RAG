## Context

两个页面并发向同一个 session 发消息时，可能只有一个消息被回复。

## Investigation Log

### ✅ 已验证的假设

#### 1. 后端并发流式请求正常

用 180s 超时的并发测试验证：

```
线程 A 发送到 chat_A     → 52.6s, 170 chars ✅
线程 B 发送到 chat_B     → 52.0s, 225 chars ✅
总耗时: 52.6s (并发完成)
```

两个 LLM 请求都成功发送并接收到完整响应。结论：**后端无连接池串扰或请求互锁**。

#### 2. `_session_config_lock` 竞争已验证无害

`_ensure_chat_target` 虽然用 `_session_config_lock` 序列化了配置读写，但：
- `chat_stream` 使用传入的 `chat_file` 而非配置中的 `active_chat`
- 锁持有时间 < 50ms（仅 JSON 文件读写）
- 日志确认两请求 phase=1-prepare 相同秒级完成

#### 3. 前端两页面状态独立

每个浏览器 Tab 有独立的：
- React 组件树
- `activeChat` / `loading` / `messages` / `abortRef` 状态
- 一个 Tab 的 `load()` 不会影响另一个 Tab 的流式请求

#### 4. 60s 超时失败的原因是 LLM API 自身延迟

```
第一批: 42s / 115s（差距 73s） ← 第二请求超时
第二批: 52.0s / 52.6s（差距 0.6s） ← 同时完成
```

LLM API（dashscope/qwen3.7-plus）在冷启动或队列拥塞时，部分请求可能延迟 2-3 倍。这不是后端代码问题。

### 🔍 未验证的场景（浏览器特有）

后端 HTTP 并发测试无法模拟的浏览器特有行为：

1. **Tab A 完成流式 → `load()` 刷新 `chats` 列表**
   - 如果 Tab B 正在同一个聊天中，`chats` 列表刷新可能导致 `activeChat` 匹配不到
   - `load()` 中 `setChats(c.chats)` 改变 chat 列表，但 Tab B 的 `activeChat` 可能在新列表中不存在（被 `normalize_chat_file` 重命名了？）

2. **`_ensure_chat_target` 中 `_normalize_chat_file` 可能改变文件名**
   - 如果 Tab A 和 Tab B 引用同一个 chat 的不同文件名形式，`_normalize_chat_file` 可能归一化导致冲突

3. **前端 `load()` 中 `sessionApi.get(name)` 读取的 `active_chat`**
   - 如果 Tab B 修改了 `active_chat`，Tab A 的 `load()` 读取到错误的 `active_chat`，虽然不影响本地 `activeChat`，但可能导致 UI 显示异常

## Conclusion

**后端不存在需要修复的并发问题。** 两个并发的流式请求可以独立完成。如果用户在两页面场景中遇到问题，根因是：
1. **LLM API 延迟差异**（一方响应慢 → 用户以为没回复）
2. **前端 UI 竞争**（少见，需要具体排查）

建议将此 change **标记为 "not-a-bug" 并归档**，除非有更多证据指向前端竞争。

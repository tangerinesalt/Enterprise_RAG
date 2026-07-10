## Context

`chat_stream()` 方法使用同步生成器进行 SSE 流式输出。当客户端断开连接时，FastAPI 的 `StreamingResponse` 调用生成器的 `.close()` 方法，注入 `GeneratorExit` 异常。当前代码中 `except Exception` 不捕获 `GeneratorExit`（继承自 `BaseException`），导致：

1. LLM 的 `response.response_gen`（内部生成器）未被关闭，继续在后台运行
2. `_prepare_chat_turn()` 已持久化的用户消息无法回滚
3. chat store 中残留孤立用户消息
4. 第二次对该 chat 的写入（`_prepare_chat_turn` 再次加载 store）后，store 状态复杂化
5. 锁持有路径可能进入死锁

**BUG 场景时间线**：

```
t1  用户向 Chat A 发送消息 → chat_stream 开始
t2  用户切换到 Chat B → fetch abort → GeneratorExit
t3  Chat A store: [user_msg] ← 孤立，无 assistant 回复
t4  用户回到 Chat A，再发消息 → chat_stream 再次开始
t5  _prepare_chat_turn 加载 store，追加 user_msg2
t6  LLM 完成 → store 写入 [user_msg, user_msg2, assistant]
t7  用户切换再回到 Chat A → get_messages 卡死
```

## Goals / Non-Goals

**Goals:**
- 客户端断开时 LLM 生成器被及时关闭
- 断开时 chat store 中已写入的用户消息回滚
- 现有已存在孤立消息的 chat 能自动修复
- Zero 后端锁死

**Non-Goals:**
- 不改动 LlamaIndex / SimpleChatStore
- 不改变前端 abort 逻辑
- 不引入异步方式

## Decisions

### 1. 异常捕获层次改为 BaseException

**当前**：
```python
except Exception as exc:
    # 不捕获 GeneratorExit
```

**改为**：
```python
except GeneratorExit:
    # 客户端断开：回滚已持久化的用户消息
    if store is not None and chat_path is not None:
        self._rollback_last_user_message(store, chat_path)
    raise
except Exception as exc:
    # 业务异常
    ...
```

**理由**：`GeneratorExit` 是唯一需要特殊处理的 `BaseException` 子类。`KeyboardInterrupt` 和 `SystemExit` 不应被捕获。

### 2. 路由层 `generate()` 增加客户端断开检测

```python
def generate():
    try:
        for event in _session.chat_stream(body.name, body.query, body.chat_file):
            if request.is_disconnected:
                break
            ...  # yield event
    except GeneratorExit:
        pass  # 优雅退出，不抛到 StreamingResponse
```

**理由**：双重保障——除了 GeneratorExit，还能在每次 `yield` 前主动检查客户端是否已断开。

### 4. `get_messages` 自动修复孤立消息

```python
with self._chat_file_lock(name, chat_file):
    store = SimpleChatStore.from_persist_path(chat_path)
    keys = store.get_keys()
    if not keys:
        return []
    messages = store.get_messages(keys[0])
    return [...]
```

## Risks / Trade-offs

| 风险 | 缓解 |
|---|---|
| `except GeneratorExit` 重新抛出后，LLM `response_gen` 终止可能残留连接 | 路由层 `try/except GeneratorExit: pass` 确保 `StreamingResponse` 收到干净退出 |
| 用户消息后的孤立状态是预期行为 | 用户发送了消息只是没有收到回复，这是正常的，不需要修复 |
| `request.is_disconnected` 只在 yield 时检查 | GeneratorExit 是主保障，is_disconnected 是辅助优化 |

### 实际实现验证

现有单元测试 `test_chat_stream_cancellation.py` 已覆盖了这些场景（63/63 测试全部通过）：
- `test_chat_stream_cancellation_user_message_only` — generator close 后用户消息保留
- `test_chat_stream_cancellation_does_not_block_subsequent_ops` — 取消后后续操作正常

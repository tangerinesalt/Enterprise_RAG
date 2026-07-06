## Why

当前项目已经支持“一个会话下多个聊天文件”的数据结构，但后端仍然把 `chat()`、`chat_stream()`、`new_chat()`、`select_chat()` 等路径统一串行化到同一把会话锁上，导致同一会话下的不同聊天无法并行对话。随着用户开始同时打开多个前端页面，现状已经直接限制了多人协作和多窗口使用体验，因此需要把并发边界从“会话”细化到“聊天”，并同步收敛 `active_chat` 的共享语义。

## What Changes

- 将当前“每会话一把锁”的模型拆分为两类锁：
  - 会话配置锁：只保护 `config.json` 的读改写与会话级元数据更新
  - 聊天文件锁：只保护 `sessions/<name>/chats/<chat_file>.json` 的消息追加与持久化
- 允许同一会话下、不同 `chat_file` 的 `chat()` / `chat_stream()` 并行执行，不再因为共享会话锁而彼此阻塞。
- 保留同一 `chat_file` 内的串行化保证，避免多人同时向同一聊天文件写入时出现消息交错、持久化覆盖或上下文错乱。
- 弱化后端 `active_chat` 作为“会话级唯一当前聊天”的语义，将其降级为兼容性/最近一次选择字段；前端页面改为以本地选中的 `chat_file` 作为真实当前聊天状态。
- 调整会话页与会话 API 的交互约定，减少“两个页面在同一会话下切换聊天互相覆盖”的行为。
- 增加并发回归测试，覆盖：
  - 同一会话不同聊天可并行
  - 同一聊天仍然串行
  - `active_chat` 降级后多人使用不再依赖全局共享当前聊天

## Capabilities

### New Capabilities
- `session-chat-concurrency`: 定义同一会话内“会话配置锁 + 聊天文件锁”的并发边界，以及不同聊天可并行、同一聊天仍串行的行为保证

### Modified Capabilities
- `session-chat`: 调整聊天执行语义，使同一会话下不同聊天文件可并行执行，同时保持单聊天上下文一致性
- `session-management`: 调整会话级 `active_chat` 的定位，弱化其作为多人共享真相的职责
- `api-session`: 调整会话聊天与聊天切换接口契约，使客户端更稳定地显式围绕 `chat_file` 工作
- `ui-session-page`: 调整会话页状态管理，改为本地维护当前聊天，避免多个页面通过共享 `active_chat` 互相覆盖
- `auto-test`: 增加针对同会话并发聊天与聊天级锁边界的自动化回归要求

## Impact

- 后端模块：`app/modules/session/session_manager.py`、`app/api/routers/session.py` 及相关会话 API schema/调用路径
- 前端模块：`ui/src/pages/SessionChat.tsx`、`ui/src/components/SessionSidebar*`、`ui/src/api/index.ts` 及相关聊天切换逻辑
- 测试：新增/扩展 `tests/unit`、必要时补充 `tests/integration`，覆盖锁边界、并发行为和页面状态语义
- 数据与协议：`sessions/<name>/config.json` 中 `active_chat` 的语义将弱化；接口层将更明确围绕 `chat_file` 而非“会话级唯一当前聊天”展开

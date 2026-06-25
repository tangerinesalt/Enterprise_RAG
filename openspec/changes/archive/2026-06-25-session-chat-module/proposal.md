## Why

目前项目只支持文档管理和检索（knowledge base），缺少与用户交互的聊天能力。需要一个会话模块，让用户可以创建会话、绑定知识库、进行多轮对话，并将每次对话记录持久化到文件，便于后续查阅和调试。

## What Changes

- 新增 `app/modules/session/` 模块（SessionManager 类）
- 新增 `sessions/` 根目录，存储所有会话数据
- 会话管理：
  - `session create <name>` — 创建会话
  - `session delete <name> [chat_file]` — 删除会话/单条聊天
  - `session bind <name> <kb_name>` — 绑定知识库
  - `session list [name]` — 列出会话/聊天文件
  - `session info <name>` — 会话详情
- 聊天管理：
  - `session new <name>` — 新建聊天文件（设为当前）
  - `session select <name> <chat_file>` — 切换到历史聊天
  - `session chat <name> [--file <chat_file>] "问题"` — 指定聊天继续/自动新建聊天
- 聊天文件命名：`年_月_日_时_分.json`，同名冲突自动加 `_1`, `_2` 后缀
- 使用 LlamaIndex `SimpleChatStore` 管理聊天记录
- config.json 记录 `kb_name` 和 `active_chat`

## Capabilities

### New Capabilities
- `session-management`: 会话的创建、绑定、删除、详情查看
- `session-chat`: 基于 SimpleChatStore 的聊天持久化与检索增强生成

### Modified Capabilities

- 无

## Impact

- 新增 `app/modules/session/session_manager.py`
- 新增 `app/modules/session/__init__.py`
- 修改 `app/modules/kb_manager/cli.py` — 添加 `session` 子命令组
- 新增 `sessions/` 根目录（加入 .gitignore）

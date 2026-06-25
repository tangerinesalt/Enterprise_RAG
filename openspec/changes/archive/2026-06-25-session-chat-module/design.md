## Context

目前可以通过 `kb upload` + `kb index` 管理文档，通过 `test/test_retrieve.py` 测试检索。现在需要将会话管理与聊天能力工程化，支持多轮对话、聊天文件切换、数据持久化。

## Goals / Non-Goals

**Goals:**
- 会话 CRUD：创建、绑定、删除、详情
- 聊天管理：新建、切换、列出、删除
- 检索增强聊天：检索绑定 KB → LLM 生成 → 持久化 → print
- 聊天文件按时间自动命名，冲突自动处理
- 通过 SimpleChatStore 管理聊天记录
- CLI 集成到现有入口

**Non-Goals:**
- 不做多用户/权限隔离
- 不做流式输出

## 存储结构

```
sessions/
└── <session_name>/
    ├── config.json
    │   {
    │     "kb_name": "my-docs",
    │     "active_chat": "2026_06_25_10_30.json"
    │   }
    └── chats/
        ├── 2026_06_25_10_30.json
        └── 2026_06_25_10_30_1.json
```

- 每个会话独立文件夹
- config.json 记录绑定的知识库和当前选中的聊天文件
- 每个 JSON 文件是一条独立的对话记录（SimpleChatStore）

## 聊天文件命名

格式：`年_月_日_时_分.json`
冲突处理：`年_月_日_时_分_1.json`、`_2.json` ...

## CLI 命令

### 会话管理

| 命令 | 功能 |
|------|------|
| `session create <name>` | 创建会话 |
| `session bind <name> <kb>` | 绑定知识库 |
| `session delete <name>` | 删除整个会话 |
| `session delete <name> <chat_file>` | 删除单条聊天 |
| `session list` | 列出所有会话 |
| `session list <name>` | 列出会话的聊天文件 |
| `session info <name>` | 会话详情（KB、active_chat、文件数） |

### 聊天操作

| 命令 | 功能 |
|------|------|
| `session new <name>` | 新建聊天文件（设为 active_chat） |
| `session select <name> <chat_file>` | 切换到历史聊天（更新 active_chat） |
| `session chat <name> "问题"` | 自动新建聊天 + 检索生成 |
| `session chat <name> --file <chat_file> "问题"` | 在指定聊天中继续 |

## 聊天流程

```
session chat my-session "什么是A1？"
  → config.json 无 active_chat → 自动新建 2026_06_25_10_30.json
  → 设为 active_chat
  → 新 SimpleChatStore → 追加用户消息
  → 加载 KB 的 ChromaDB → 检索 top-5
  → LLM 生成回答 → 追加助手消息（含来源）
  → persist → print
```

```
session chat my-session --file 2026_06_25_10_30.json "接着说"
  → 加载该文件 SimpleChatStore（恢复历史上下文）
  → 追加用户消息 → 检索 → 生成 → 追加回答
  → persist → print
```

## SessionManager 方法

```python
class SessionManager:
    create(name)
    delete(name, chat_file=None)
    bind(name, kb_name)
    info(name) -> dict
    list_all() -> list
    list_chats(name) -> list
    new_chat(name) -> str         # 返回新文件名
    select_chat(name, chat_file)
    chat(name, query, chat_file=None) -> dict
```

## 文件结构

```
app/modules/session/
├── __init__.py
└── session_manager.py
```

## 风险

- 多轮上下文超长 → 后续加截断
- 同一分钟多次新建 → 后缀机制解决

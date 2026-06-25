## Context

项目已有完整的 CLI 功能（kb_manager + session），Web 化需要将现有能力通过 REST API 暴露。业务逻辑全部在 `app/modules/` 中，API 层只做 HTTP 包装，不修改现有代码。

## Goals / Non-Goals

**Goals:**
- FastAPI 应用能启动，CORS 已配置
- 知识库 CRUD：创建、列表、详情、删除
- 聊天功能：创建会话、绑定 KB、发起聊天、列出聊天文件
- 所有 API 通过 curl 可验证
- 不修改 app/modules/ 现有代码

**Non-Goals:**
- 不做用户认证/权限
- 不做流式输出（后续加）
- 不做前端（后续 change）

## Decisions

### 1. API 路由设计

```
GET    /api/kb                         列知识库
POST   /api/kb                         创建知识库  body: {name}
GET    /api/kb/{name}                  知识库详情
POST   /api/kb/upload                  上传文件/文件夹（multipart）
POST   /api/kb/index                   索引 body: {name, target, all?}
POST   /api/kb/reindex                 重新索引 body: {name, filename}
POST   /api/kb/upload-and-index        上传+索引（multipart）
DELETE /api/kb/{name}                  删除知识库

GET    /api/session                    列会话
POST   /api/session                    创建会话  body: {name}
GET    /api/session/{name}             会话详情
DELETE /api/session/{name}             删除会话
POST   /api/session/bind               绑定 KB   body: {name, kb_name}
POST   /api/session/new                新建聊天 body: {name}
POST   /api/session/select             切换聊天 body: {name, chat_file}
POST   /api/session/chat               聊天     body: {name, query, chat_file?}
GET    /api/session/{name}/chats       聊天文件列表
```

### 2. 聊天 API 逻辑

`POST /api/session/chat` 直接调用 `SessionManager.chat()`，它内部已完成：

```
接收参数 → SessionManager.chat()
  → 加载 config（KB、active_chat）
  → 加载 SimpleChatStore（历史上下文）
  → 加载 ChromaDB → 检索
  → LLM 生成
  → 写入 SimpleChatStore（持久化）
  → 返回 {answer, sources, chat_file}
→ 返回 JSON 给前端
```

### 3. 文件结构

```
app/api/
├── __init__.py
├── server.py           # FastAPI app + CORS
├── schemas.py           # Pydantic 模型
└── routers/
    ├── __init__.py
    ├── kb.py            # 知识库路由
    └── session.py       # 会话路由
```

### 4. 依赖

```
fastapi, uvicorn  ← requirements-web.txt
```

## API 响应格式

所有接口统一返回：

```json
// 成功
{"ok": true, "data": ...}

// 错误
{"ok": false, "error": "错误信息"}
```

## Risks

- SessionManager 文件操作非线程安全 → 单线程 uvicorn 运行无问题，多 worker 需后续改造
- 无认证 → 局域网使用可接受，暴露公网需加 auth

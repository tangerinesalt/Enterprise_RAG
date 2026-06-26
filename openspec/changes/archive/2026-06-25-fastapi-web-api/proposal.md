## Why

当前项目功能完整（知识库管理 + 会话聊天），但只有 CLI 入口，使用门槛高。需要提供 Web 界面让非技术用户也能使用 RAG 能力。先用 FastAPI 将现有模块能力暴露为 REST API，为后续 React 前端提供后端基础。

## What Changes

- 新增 `app/api/server.py` — FastAPI 应用入口
- 新增 `app/api/routers/` — kb 和 session 的路由模块
- 新增 `app/api/schemas.py` — Pydantic 请求/响应模型
- 实现 REST API：
  - `GET /api/kb` — 列出所有知识库
  - `GET /api/kb/{name}` — 知识库详情（文件列表）
  - `POST /api/kb` — 创建知识库
  - `POST /api/kb/upload` — 上传文件/文件夹（multipart）
  - `POST /api/kb/index` — 索引文件/文件夹
  - `POST /api/kb/reindex` — 重新索引文件
  - `POST /api/kb/upload-and-index` — 上传+索引一步
  - `DELETE /api/kb/{name}` — 删除知识库
  - `GET /api/session` — 列出所有会话
  - `GET /api/session/{name}` — 会话详情
  - `POST /api/session` — 创建会话
  - `POST /api/session/bind` — 绑定知识库
  - `POST /api/session/new` — 新建聊天
  - `POST /api/session/select` — 切换聊天
  - `POST /api/session/chat` — 聊天接口（核心）
  - `GET /api/session/{name}/chats` — 列出聊天文件
  - `DELETE /api/session/{name}` — 删除会话
- 新增 `requirements-web.txt` — Web 相关依赖（fastapi, uvicorn）
- `app/modules/` 下的业务代码**不修改**，API 层只做 HTTP 包装

## Capabilities

### New Capabilities
- `api-kb`: 知识库 REST API（CRUD + 文件列表）
- `api-session`: 会话 REST API（CRUD + 绑定 + 聊天）
- `api-server`: FastAPI 应用入口与 CORS 配置

### Modified Capabilities

- 无（不修改现有模块代码）

## Impact

- 新增 `app/api/server.py`
- 新增 `app/api/__init__.py`
- 新增 `app/api/routers/__init__.py`
- 新增 `app/api/routers/kb.py`
- 新增 `app/api/routers/session.py`
- 新增 `app/api/schemas.py`
- 新增 `requirements-web.txt`
- 依赖：fastapi, uvicorn

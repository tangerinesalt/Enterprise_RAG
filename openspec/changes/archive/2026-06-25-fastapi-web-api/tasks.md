## 1. 安装依赖与骨架

- [x] 1.1 安装 fastapi / uvicorn
- [x] 1.2 创建 `app/api/` 结构（server.py + schemas.py + routers/）
- [x] 1.3 实现 `server.py`：FastAPI app + CORS + health check
- [x] 1.4 创建 `requirements-web.txt`

## 2. 知识库 API

- [x] 2.1 实现 `routers/kb.py`：`GET /api/kb` 列表
- [x] 2.2 实现 `POST /api/kb` 创建
- [x] 2.3 实现 `GET /api/kb/{name}` 详情
- [x] 2.4 实现 `POST /api/kb/upload` 上传文件/文件夹（multipart）
- [x] 2.5 实现 `POST /api/kb/index` 索引文件/文件夹
- [x] 2.6 实现 `POST /api/kb/reindex` 重新索引
- [x] 2.7 实现 `POST /api/kb/upload-and-index` 上传+索引
- [x] 2.8 实现 `DELETE /api/kb/{name}` 删除

## 3. 会话 API

- [x] 3.1 实现 `routers/session.py`：`GET /api/session` 列表
- [x] 3.2 实现 `POST /api/session` 创建
- [x] 3.3 实现 `GET /api/session/{name}` 详情
- [x] 3.4 实现 `DELETE /api/session/{name}` 删除
- [x] 3.5 实现 `POST /api/session/bind` 绑定知识库
- [x] 3.6 实现 `POST /api/session/new` 新建聊天
- [x] 3.7 实现 `POST /api/session/select` 切换聊天
- [x] 3.8 实现 `POST /api/session/chat` 聊天（核心）
- [x] 3.9 实现 `GET /api/session/{name}/chats` 聊天文件列表

## 4. 验证

- [x] 4.1 启动服务器：`uvicorn app.api.server:app --reload --port 8000`
- [x] 4.2 curl 测试知识库 API（创建/上传/索引 ✅）
- [x] 4.3 curl 测试会话 API（创建/绑定/聊天 ✅）
- [x] 4.4 curl 测试聊天：返回回答和来源 ✅

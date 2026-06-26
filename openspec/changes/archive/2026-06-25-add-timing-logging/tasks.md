## 1. 后端计时工具

- [x] 1.1 创建 `app/utils/__init__.py` + `app/utils/timing.py`（`@timed` 装饰器 + 最近请求存储）
- [x] 1.2 支持彩色终端输出（OK/WARN/ERROR 三级阈值）

## 2. API 层接入计时

- [x] 2.1 `app/api/server.py` 添加请求中间件记录全请求耗时
- [x] 2.2 `app/api/server.py` 添加 `GET /api/performance` 端点
- [x] 2.3 `routers/kb.py` 关键操作（upload/index/delete）添加 `@timed`
- [x] 2.4 `routers/session.py` 关键操作（chat/bind/delete）添加 `@timed`

## 3. 模型调用计时

- [ ] 3.1 `indexer.py` 中 Embedding 调用添加计时（需评估 - 目前通过中间件可见）
- [x] 3.2 `session_manager.py` 中 chat 流程分阶段计时（检索/生成/持久化）

## 4. 前端请求日志

- [x] 4.1 `ui/src/api/index.ts` 每个请求记录 `[API] METHOD /path → Xms`
- [x] 4.2 超过 1s 的请求输出 `[API][SLOW]` 警告

## 5. 验证

- [x] 5.1 启动服务，切换页面查看终端日志（中间件 + @timed 均输出）
- [x] 5.2 发起聊天，观察分阶段耗时（load_history / retrieval+generation / persist）
- [ ] 5.3 浏览器 DevTools 控制台查看前端日志（需配合前端启动）

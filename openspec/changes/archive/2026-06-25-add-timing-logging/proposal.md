## Why

用户在使用过程中感知到操作延迟（如切换页面 0.5s），但无法确定瓶颈在后端 API、Ollama 模型、还是前端渲染。需要运行时日志和时序数据来定位问题，为性能优化提供数据依据。

## What Changes

- 后端 API 添加耗时日志装饰器，自动记录每个请求的处理时间
- Ollama Embedding / Chat 调用添加独立计时日志
- 后端添加简单的 `/api/performance` 端点返回最近请求的耗时统计
- 前端添加 API 请求耗时控制台日志，可在 DevTools 中查看
- 请求耗时超过阈值的操作标红（>1s 警告，>5s 错误）

## Capabilities

### New Capabilities
- `api-timing-log`: 后端 API 请求耗时日志与统计
- `frontend-timing-log`: 前端 API 请求耗时记录

### Modified Capabilities

- 无

## Impact

- 新增 `app/utils/timing.py` — 耗时日志装饰器
- 修改 `app/api/server.py` — 注册中间件记录全请求耗时
- 修改 `app/api/routers/kb.py` / `session.py` — 关键操作添加独立计时
- 修改 `app/modules/kb_manager/indexer.py` — Embedding 调用计时
- 修改 `app/modules/session/session_manager.py` — chat 流程分段计时
- 修改 `ui/src/api/index.ts` — 前端请求耗时日志

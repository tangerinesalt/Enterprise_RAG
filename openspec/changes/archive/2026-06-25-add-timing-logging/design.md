## Context

用户反馈页面切换和操作有可见延迟，但后端纯文件操作实测仅 2-6ms，Ollama 调用 3-10 秒属正常。需要工具量化每步耗时，区分"前端渲染"、"后端处理"、"模型推理"各占多少。

## Goals / Non-Goals

**Goals:**
- 每个 HTTP 请求记录总耗时
- Ollama Embedding 和 Chat 调用独立计时
- 前端每个 API 请求记录耗时到浏览器 console
- 耗时可视化：终端彩色输出，超过阈值高亮
- 提供 `/api/performance` 查看最近请求统计

**Non-Goals:**
- 不做 APM 或持久化监控
- 不做分布式追踪

## Decisions

### 1. 后端计时装饰器 `@timed()`

```python
# app/utils/timing.py
import time
from functools import wraps

# 存储最近请求耗时
_recent_requests = []

def timed(label=None, warn=1.0, error=5.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            t0 = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.time() - t0
                _recent_requests.append({"label": label or func.__name__, "elapsed": elapsed})
                # 彩色输出
                if elapsed > error:
                    print(f"\033[91m[TIMING][ERROR] {label}: {elapsed:.2f}s\033[0m")
                elif elapsed > warn:
                    print(f"\033[93m[TIMING][WARN] {label}: {elapsed:.2f}s\033[0m")
                else:
                    print(f"\033[92m[TIMING][OK] {label}: {elapsed:.3f}s\033[0m")
        return wrapper
    return decorator
```

### 2. FastAPI 中间件——记录全请求耗时

```python
# app/api/server.py
@app.middleware("http")
async def timing_middleware(request, call_next):
    t0 = time.time()
    response = await call_next(request)
    elapsed = time.time() - t0
    print(f"[TIMING] {request.method} {request.url.path} → {elapsed:.3f}s")
    return response
```

### 3. 性能统计端点

`GET /api/performance` 返回最近 100 条请求的耗时列表和聚合统计。

### 4. 前端 API 封装增加耗时日志

```typescript
// ui/src/api/index.ts
async function req<T>(url: string, options?: RequestInit): Promise<T> {
  const t0 = performance.now();
  const res = await fetch(...);
  const elapsed = performance.now() - t0;
  console.log(`[API] ${options?.method || 'GET'} ${url} → ${elapsed.toFixed(0)}ms`);
  if (elapsed > 1000) console.warn(`[API][SLOW] ${url} took ${elapsed.toFixed(0)}ms`);
  return data.data;
}
```

## 输出效果

```
后端终端：
  [TIMING] GET /api/kb → 0.003s
  [TIMING] GET /api/session/msg-test/chats → 0.001s
  [TIMING][OK] index_file: 3.204s
  [TIMING][OK] ollama_chat: 8.451s

浏览器 DevTools 控制台：
  [API] GET /api/session → 5ms
  [API] GET /api/session/msg-test/chats → 3ms
  [API] POST /api/session/chat → 10453ms
  [API][SLOW] POST /api/session/chat took 10453ms
```

## 文件变更

```
app/utils/
├── __init__.py
└── timing.py           # 新增：计时装饰器 + 最近请求存储

app/api/server.py       # 修改：添加请求中间件 + /api/performance 端点
app/api/routers/kb.py   # 修改：关键操作添加 @timed
app/api/routers/session.py  # 修改：关键操作添加 @timed
ui/src/api/index.ts     # 修改：前端请求耗时日志
```

## Risks

- 日志过多会刷屏 → 可加采样率或关闭开关
- 正式部署时需清理日志代码 → 通过环境变量控制是否启用

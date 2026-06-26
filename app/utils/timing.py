"""
运行时计时工具。

用法：
    @timed("ollama_chat")
    def chat():
        ...

    @timed(warn=0.5, error=3.0)
    def index_file():
        ...

    get_stats()  → 返回最近请求的耗时统计
"""

import time
from functools import wraps
from collections import deque

# 存储最近 100 条请求耗时
_recent: deque = deque(maxlen=100)


def timed(label: str = None, warn: float = 1.0, error: float = 5.0):
    """
    函数耗时装饰器。

    参数：
        label: 显示名称（默认用函数名）
        warn:  警告阈值（秒），超过显示黄色
        error: 错误阈值（秒），超过显示红色
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = label or func.__name__
            t0 = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.time() - t0
                _recent.append({
                    "label": name,
                    "elapsed": round(elapsed, 3),
                    "time": time.strftime("%H:%M:%S"),
                })
                _print_timing(name, elapsed, warn, error)
        return wrapper
    return decorator


def _print_timing(name: str, elapsed: float, warn: float, error: float):
    """彩色输出耗时信息"""
    if elapsed > error:
        level = "ERROR"
        color = "\033[91m"  # 红
    elif elapsed > warn:
        level = "WARN"
        color = "\033[93m"  # 黄
    else:
        level = "OK"
        color = "\033[92m"  # 绿
    reset = "\033[0m"
    print(f"{color}[TIMING][{level}] {name}: {elapsed:.3f}s{reset}")


def get_stats() -> dict:
    """获取最近请求的耗时统计"""
    items = list(_recent)
    if not items:
        return {"total": 0, "items": []}

    times = [i["elapsed"] for i in items]
    return {
        "total": len(items),
        "avg": round(sum(times) / len(times), 3),
        "max": round(max(times), 3),
        "min": round(min(times), 3),
        "items": items[-50:],  # 最近 50 条
    }

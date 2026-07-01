"""Application logging helpers."""

import logging
import os


_CONFIGURED = False


def _configured_level() -> str:
    """Return the configured app log level."""
    value = os.environ.get("RAGV_LOG_LEVEL") or os.environ.get("LOG_LEVEL")
    if value:
        return value.upper()

    try:
        from config.settings import load_settings

        settings = load_settings().get("env", {})
        value = settings.get("RAGV_LOG_LEVEL") or settings.get("LOG_LEVEL")
        if value:
            return str(value).upper()
    except Exception:
        pass

    return "INFO"


def configure_logging() -> None:
    """Configure default application logging once per process."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = _configured_level()
    level = getattr(logging, level_name, logging.INFO)

    # basicConfig 会被 uvicorn 抢先执行后静默忽略，
    # 直接用 setLevel 保证级别生效
    logging.getLogger().setLevel(level)
    logging.getLogger("app").setLevel(level)

    # 静默 httpx 库的 HTTP 请求日志（embedding + LLM 调用）
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    # 静默 chromadb 的 INFO 噪音
    logging.getLogger("chromadb").setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)

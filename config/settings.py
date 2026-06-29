"""配置 — 从项目根目录 settings.json 读取运行时参数。"""

import json
import os
from pathlib import Path


def _find_project_root() -> Path:
    """从当前文件向上找，直到找到 settings.json"""
    p = Path(__file__).resolve()
    for parent in [p] + list(p.parents):
        if (parent / "settings.json").exists():
            return parent
    # fallback: cwd
    return Path.cwd()


_PROJECT_ROOT = _find_project_root()
_SETTINGS_PATH = _PROJECT_ROOT / "settings.json"


def load_settings() -> dict:
    if not _SETTINGS_PATH.exists():
        return {}
    with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_raw = load_settings().get("env", {})

# ── LLM 提供商配置 ──────────────────────────
LLM_PROVIDER = (_raw.get("LLM_PROVIDER") or "ollama").lower().strip()

# LLM_* 标准键，向后兼容 ES_* 旧键
LLM_URL = (_raw.get("LLM_URL") or "http://127.0.0.1:11434").rstrip("/")
LLM_MODEL = (_raw.get("LLM_MODEL")  or "qwen3.5:9b")
LLM_TOKEN = _raw.get("LLM_TOKEN")  or ""

# 便捷别名（保留向后兼容）
OLLAMA_URL = LLM_URL

# ── Embedding 配置 ──────────────────────────
EMBED_URL = _raw.get("EMBED_URL", "http://127.0.0.1:11434").rstrip("/")
EMBED_MODEL = _raw.get("EMBED_MODEL", "qwen3-embedding:4b")

# 知识库根目录
KB_ROOT = str((_PROJECT_ROOT / "kb").resolve())

# OCR
ENABLE_OCR_FALLBACK = True

# 分块策略
CHUNK_SIZE = 512
CHUNK_OVERLAP = 128
CHUNK_PARAGRAPH_SEPARATOR = "\n\n"

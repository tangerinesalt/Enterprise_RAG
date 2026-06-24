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

OLLAMA_URL = _raw.get("ES_URL", "http://127.0.0.1:11434").rstrip("/")
LLM_MODEL = _raw.get("ES_MODEL", "qwen3.5:9b")
EMBED_URL = _raw.get("EMBED_URL", "http://127.0.0.1:11434").rstrip("/")
EMBED_MODEL = _raw.get("EMBED_MODEL", "qwen3-embedding:4b")
API_TOKEN = _raw.get("ES_TOKEN", "")

# 知识库根目录
KB_ROOT = str((_PROJECT_ROOT / "kb").resolve())

# OCR
ENABLE_OCR_FALLBACK = True

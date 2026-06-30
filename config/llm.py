"""LLM 全局配置。

调用 init_llm() 后，Settings.llm 全局就绪。
根据 LLM_PROVIDER 选择不同的 LLM 实现。

支持 provider:
  - ollama   (默认，本地 Ollama)
  - deepseek (DeepSeek API, OpenAI-compatible)
  - openai   (OpenAI API)
"""

from llama_index.core import Settings
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI as OpenAILI

from config.settings import LLM_PROVIDER, LLM_URL, LLM_MODEL, LLM_TOKEN


def init_llm():
    """根据 LLM_PROVIDER 初始化全局 LLM。"""
    provider = LLM_PROVIDER

    if provider == "ollama":
        Settings.llm = Ollama(
            model=LLM_MODEL,
            base_url=LLM_URL,
            temperature=0.3,
            request_timeout=60,
        )

    elif provider == "deepseek":
        if not LLM_TOKEN:
            raise ValueError(
                "DeepSeek 需要配置 LLM_TOKEN。"
                "请在 settings.json 中设置 LLM_TOKEN 或 ES_TOKEN。"
            )
        # DeepSeek 专用默认值，不继承 Ollama 的 fallback
        ds_model = LLM_MODEL if LLM_MODEL not in ("", "qwen3.5:9b") else "deepseek-chat"
        ds_url = LLM_URL if LLM_URL not in ("", "http://127.0.0.1:11434") else "https://api.deepseek.com/v1"
        llm = OpenAILI(
            model="gpt-4o",  # 占位：仅用于绕过 LlamaIndex 模型名校验
            api_key=LLM_TOKEN,
            api_base=ds_url,
            temperature=0.7,
            request_timeout=60,
            strict=False,
        )
        llm.model = ds_model  # 替换为实际模型名
        # 让 _get_model_name 返回已知模型名，避免 context_window 查询失败
        llm._get_model_name = lambda: "gpt-4o"
        Settings.llm = llm

    elif provider == "openai":
        if not LLM_TOKEN:
            raise ValueError(
                "OpenAI 需要配置 LLM_TOKEN。"
                "请在 settings.json 中设置 LLM_TOKEN。"
            )
        Settings.llm = OpenAILI(
            model=LLM_MODEL or "gpt-4o",
            api_key=LLM_TOKEN,
            api_base=LLM_URL or "https://api.openai.com/v1",
            temperature=0.5,
            request_timeout=60,
        )

    else:
        raise ValueError(
            f"不支持的 LLM_PROVIDER: '{provider}'。"
            f"支持的 provider: ollama, deepseek, openai"
        )

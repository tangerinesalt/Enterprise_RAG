"""LLM 全局配置。

调用 init_llm() 后，Settings.llm 全局就绪。
更换模型只需修改此文件，无需改动消费代码。
"""

from llama_index.core import Settings
from llama_index.llms.ollama import Ollama

from config.settings import OLLAMA_URL, LLM_MODEL


def init_llm():
    """初始化全局 LLM。"""
    Settings.llm = Ollama(
        model=LLM_MODEL,
        base_url=OLLAMA_URL,
        temperature=0.3,
        request_timeout=60,
    )

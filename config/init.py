"""统一模型初始化入口。

使用方式：
    from config.init import init_models
    init_models()  # LLM + Embedding 全局就绪
"""

from config.embedding import init_embedding
from config.llm import init_llm


def init_models():
    """按序初始化 Embedding → LLM。"""
    init_embedding()
    init_llm()

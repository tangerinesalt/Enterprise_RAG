"""Embedding 模型全局配置。

调用 init_embedding() 后，Settings.embed_model 全局就绪。
更换模型只需修改此文件，无需改动消费代码。
"""

from llama_index.core import Settings
from llama_index.embeddings.ollama import OllamaEmbedding

from config.settings import EMBED_URL, EMBED_MODEL


def init_embedding():
    """初始化全局 Embedding 模型。"""
    Settings.embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=EMBED_URL,
    )
    # 全局关闭 tqdm 进度条（检索阶段的 embedding 不刷屏）
    Settings.show_progress = False

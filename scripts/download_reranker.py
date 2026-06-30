"""
下载 BAAI/bge-reranker-v2-m3 模型到本地 models/ 目录。

用法：
    python scripts/download_reranker.py

模型约 2.2GB，首次下载需保证网络稳定。
下载完成后，修改 app/modules/session/session_manager.py 第 296 行：
    rerank = SentenceTransformerRerank(model="BAAI/bge-reranker-v2-m3", top_n=top_n)
改为：
    rerank = SentenceTransformerRerank(
        model="C:/Users/tangerine/.rag_v/models/BAAI/bge-reranker-v2-m3",
        top_n=top_n,
    )
"""

import os
from pathlib import Path

# 下载到项目 models/ 目录（已在 .gitignore 中忽略）
MODEL_NAME = "BAAI/bge-reranker-v2-m3"
LOCAL_DIR = Path(__file__).resolve().parent.parent / "models" / MODEL_NAME


def main():
    print(f"下载模型: {MODEL_NAME}")
    print(f"保存到:   {LOCAL_DIR}")
    print(f"大小:     ~2.2GB")
    print()

    from huggingface_hub import snapshot_download

    os.makedirs(LOCAL_DIR.parent, exist_ok=True)
    snapshot_download(
        MODEL_NAME,
        local_dir=str(LOCAL_DIR),
        local_dir_use_symlinks=False,
    )

    print()
    print("下载完成！")
    print(f"模型位置: {LOCAL_DIR}")
    print()
    print("使用方式：")
    print("  rerank = SentenceTransformerRerank(")
    print(f'      model=r"{LOCAL_DIR}",')
    print("      top_n=top_n,")
    print("  )")


if __name__ == "__main__":
    main()

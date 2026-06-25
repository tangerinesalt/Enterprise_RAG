"""
CLI — 顶层入口。

将命令分发给对应模块：
    kb       → 知识库管理 (kb_manager)
    session  → 会话与聊天管理 (session)

用法：
    python -m app.cli kb create <name>
    python -m app.cli session chat <name> "问题"
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="RAG V — 企业级 RAG 应用",
        epilog="""
常用命令:
  app.cli kb create <name>                    创建知识库
  app.cli kb upload <name> <path>             上传文件/文件夹
  app.cli kb index <name> <target|--all>      索引
  app.cli kb list                              列出知识库
  app.cli session create <name>               创建会话
  app.cli session bind <name> <kb>            绑定知识库
  app.cli session chat <name> "问题"           聊天
  app.cli session list                         列出会话
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("command", choices=["kb", "session"],
                        help="kb — 知识库管理（上传/索引/删除）  session — 会话与聊天")

    # 只解析顶层命令，剩余参数全部透传给子 CLI
    parsed, unknown = parser.parse_known_args()

    if parsed.command == "kb":
        from app.modules.kb_manager import cli as kb_cli
        target_cli = kb_cli
    else:
        from app.modules.session import cli as session_cli
        target_cli = session_cli

    # 透传所有剩余参数
    sys.argv = [sys.argv[0]] + unknown
    target_cli.main()


if __name__ == "__main__":
    main()

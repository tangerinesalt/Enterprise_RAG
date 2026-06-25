"""
CLI — 会话与聊天管理子命令。

用法：
    python -m app.cli session create <name>
    python -m app.cli session bind <name> <kb>
    python -m app.cli session chat <name> [--file <f>] "<query>"
    python -m app.cli session list [name]
    python -m app.cli session info <name>
    python -m app.cli session new <name>
    python -m app.cli session select <name> <chat_file>
    python -m app.cli session delete <name> [chat_file]
"""

import argparse
import sys

# Windows 控制台 UTF-8 支持
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.modules.session import SessionManager, SessionError

_session = SessionManager()


# ── 命令处理 ─────────────────────────────────

def cmd_create(args):
    try:
        _session.create(args.name)
        print(f"[OK] 会话 '{args.name}' 已创建")
    except SessionError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_bind(args):
    try:
        _session.bind(args.name, args.kb_name)
        print(f"[OK] 会话 '{args.name}' 已绑定知识库 '{args.kb_name}'")
    except SessionError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_delete(args):
    try:
        _session.delete(args.name, args.chat_file)
        if args.chat_file:
            print(f"[OK] 已删除聊天 '{args.chat_file}'")
        else:
            print(f"[OK] 已删除会话 '{args.name}'")
    except SessionError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_info(args):
    try:
        info = _session.info(args.name)
        print(f"\n会话: {info['name']}")
        print(f"{'='*40}")
        print(f"  绑定的知识库: {info['kb_name'] or '(未绑定)'}")
        print(f"  当前聊天:     {info['active_chat'] or '(无)'}")
        print(f"  聊天总数:     {info['total_chats']}")
    except SessionError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_list(args):
    try:
        if args.chat_file:
            # 查看指定聊天的消息记录
            msgs = _session.get_messages(args.name, args.chat_file)
            if not msgs:
                print(f"聊天 '{args.chat_file}' 中没有消息")
                return
            print(f"\n聊天: {args.chat_file} ({len(msgs)} 条消息)")
            print(f"{'='*50}")
            for m in msgs:
                role = "👤 用户" if m["role"] == "user" else "🤖 助手"
                print(f"\n[{role}]")
                print("-" * 40)
                print(m["content"][:500])
                if len(m["content"]) > 500:
                    print("...")
        elif args.name:
            chats = _session.list_chats(args.name)
            if not chats:
                print(f"会话 '{args.name}' 中没有聊天记录")
                return
            print(f"\n会话 '{args.name}' 的聊天记录:")
            print(f"{'='*50}")
            for c in chats:
                marker = "* " if c["is_active"] else "  "
                print(f"  {marker}{c['file']:40s} ({c['messages']} 条消息)")
        else:
            sessions = _session.list_all()
            if not sessions:
                print("暂无会话")
                return
            print(f"\n会话列表:")
            print(f"{'='*50}")
            for s in sessions:
                kb = s['kb_name'] or '(未绑定)'
                active = s['active_chat'] or '(无)'
                print(f"  {s['name']:30s} KB: {kb:15s} 聊天: {active}")
            print(f"{'='*50}")
            print(f"共 {len(sessions)} 个会话")
    except SessionError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_new(args):
    try:
        filename = _session.new_chat(args.name)
        print(f"[OK] 已新建聊天: {filename}")
    except SessionError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_select(args):
    try:
        _session.select_chat(args.name, args.chat_file)
        print(f"[OK] 已切换到聊天: {args.chat_file}")
    except SessionError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_chat(args):
    try:
        result = _session.chat(args.name, args.query, args.file)
        print(f"\n{'='*50}")
        print(f"回答")
        print(f"{'='*50}")
        print(result["answer"])
        if result["sources"]:
            print(f"\n{'='*50}")
            print(f"参考来源")
            print(f"{'='*50}")
            for i, s in enumerate(result["sources"]):
                print(f"\n[来源 {i+1}] (相关度: {s['score']})")
                print("-" * 40)
                print(s["text"])
        print(f"\n[聊天文件: {result['chat_file']}]")
    except SessionError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


# ── 主入口 ─────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="会话与聊天管理",
        epilog="""
用法示例:
  session create my-session                   创建新会话
  session bind my-session my-docs             为会话绑定知识库
  session info my-session                     查看会话详情
  session list                                列出所有会话
  session list my-session                     列出会话的聊天记录
  session new my-session                      在会话中新建一条聊天
  session select my-session 2026_06_25.json   切换到指定聊天
  session delete my-session                   删除整个会话
  session delete my-session 2026_06_25.json   删除单条聊天
  session chat my-session "问题"              自动新建聊天并提问
  session chat my-session --file xxx.json "问" 在指定聊天中继续提问
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("create", help="创建新会话")
    p.add_argument("name", help="会话名称")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("bind", help="将会话绑定到一个知识库")
    p.add_argument("name", help="会话名称")
    p.add_argument("kb_name", help="要绑定的知识库名称")
    p.set_defaults(func=cmd_bind)

    p = sub.add_parser("delete", help="删除整个会话或单条聊天")
    p.add_argument("name", help="会话名称")
    p.add_argument("chat_file", nargs="?", default=None,
                   help="聊天文件名（省略则删除整个会话，指定则只删该聊天）")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("info", help="查看会话详细信息（KB、当前聊天、聊天数）")
    p.add_argument("name", help="会话名称")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("list", help="列出会话/聊天文件/聊天消息")
    p.add_argument("name", nargs="?", default=None, help="会话名称（可选）")
    p.add_argument("chat_file", nargs="?", default=None, help="聊天文件名（可选，查看消息内容）")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("new", help="在会话中创建一条新的聊天记录")
    p.add_argument("name", help="会话名称")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("select", help="切换到某条历史聊天（设为当前）")
    p.add_argument("name", help="会话名称")
    p.add_argument("chat_file", help="聊天文件名（如 2026_06_25_09_30.json）")
    p.set_defaults(func=cmd_select)

    p = sub.add_parser("chat", help="聊天：检索知识库 → LLM 生成 → 写入聊天记录 → 打印")
    p.add_argument("name", help="会话名称")
    p.add_argument("query", help="提问内容（自然语言）")
    p.add_argument("--file", default=None, help="指定聊天文件继续对话（省略则自动新建一条聊天）")
    p.set_defaults(func=cmd_chat)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

"""
CLI — 知识库管理命令行入口。

用法：
    python -m app.modules.kb_manager.cli kb create <name>
    python -m app.modules.kb_manager.cli kb upload <name> <path>
    python -m app.modules.kb_manager.cli kb index <name> <target|--all>
    python -m app.modules.kb_manager.cli kb upload-and-index <name> <path>
    python -m app.modules.kb_manager.cli kb delete <name> <target>
    python -m app.modules.kb_manager.cli kb reindex <name> <filename>
    python -m app.modules.kb_manager.cli kb list [name]
"""

import argparse
import os
import sys

from app.modules.kb_manager import KnowledgeBase, KnowledgeBaseError
from app.modules.kb_manager.indexer import Indexer

_kb = KnowledgeBase()
_indexer = Indexer()


def cmd_create(args):
    try:
        path = _kb.create(args.name)
        print(f"[OK] 知识库 '{args.name}' 已创建: {path}")
    except KnowledgeBaseError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_upload(args):
    """上传文件或文件夹（不自动索引）"""
    try:
        _kb.ensure_exists(args.name)

        if not os.path.exists(args.path):
            print(f"[ERROR] 路径不存在: {args.path}")
            sys.exit(1)

        if os.path.isfile(args.path):
            # 上传单个文件
            _kb.copy_file(args.name, args.path)
            filename = os.path.basename(args.path)
            print(f"[OK] 已复制: {filename}")
            print(f"      路径: {_kb.file_path(args.name, filename)}")
            print(f"      提示: 运行 'kb index {args.name} {filename}' 来索引")

        elif os.path.isdir(args.path):
            # 上传文件夹
            files = _kb.upload_folder(args.name, args.path)
            folder_name = os.path.basename(os.path.normpath(args.path))
            print(f"[OK] 已复制文件夹 '{folder_name}'（{len(files)} 个文件）")
            print(f"      提示: 运行 'kb index {args.name} {folder_name}' 来索引")

    except KnowledgeBaseError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_index(args):
    """索引文件或文件夹"""
    try:
        _kb.ensure_exists(args.name)

        if args.all:
            # 索引所有文件
            print(f"[索引] 正在索引 '{args.name}' 中所有文件...")
            results = _indexer.index_all(args.name)
            _print_index_results(results)

        elif _kb.folder_exists(args.name, args.target):
            # 索引文件夹
            print(f"[索引] 正在索引文件夹 '{args.target}'...")
            results = _indexer.index_folder(args.name, args.target)
            _print_index_results(results)

        elif _kb.file_exists(args.name, args.target):
            # 索引单个文件
            print(f"[索引] 正在索引 '{args.target}'...")
            count = _indexer.index_file(args.name, args.target)
            print(f"[OK] 索引完成: {args.target}（{count} 个块）")

        else:
            print(f"[ERROR] '{args.target}' 不存在于知识库 '{args.name}' 中")
            sys.exit(1)

    except (KnowledgeBaseError, FileNotFoundError) as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_upload_and_index(args):
    """上传+索引一步完成"""
    try:
        _kb.ensure_exists(args.name)

        if not os.path.exists(args.path):
            print(f"[ERROR] 路径不存在: {args.path}")
            sys.exit(1)

        if os.path.isfile(args.path):
            _kb.copy_file(args.name, args.path)
            filename = os.path.basename(args.path)
            print(f"[上传] 已复制: {filename}")
            print(f"[索引] 正在索引...")
            count = _indexer.index_file(args.name, filename)
            print(f"[OK] 上传并索引完成: {filename}（{count} 个块）")

        elif os.path.isdir(args.path):
            folder_name = os.path.basename(os.path.normpath(args.path))
            files = _kb.upload_folder(args.name, args.path)
            print(f"[上传] 已复制文件夹 '{folder_name}'（{len(files)} 个文件）")
            print(f"[索引] 正在索引文件夹...")
            results = _indexer.index_folder(args.name, folder_name)
            _print_index_results(results)

    except (KnowledgeBaseError, FileNotFoundError) as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_delete(args):
    """删除文件、文件夹或整个知识库"""
    try:
        if args.target is None:
            # 删除整个知识库
            name = args.name
            _kb.destroy(name)
            print(f"[OK] 已删除知识库 '{name}'")
            return

        _kb.ensure_exists(args.name)

        if _kb.folder_exists(args.name, args.target):
            # 删除文件夹
            files = _kb.list_folder_files(args.name, args.target)
            vec_total = 0
            for rel_path in files:
                deleted = _indexer.delete_vectors(args.name, rel_path)
                vec_total += deleted
                _kb.remove_file(args.name, rel_path)
            _kb.delete_folder(args.name, args.target)
            print(f"[OK] 已删除文件夹 '{args.target}'"
                  f"（{len(files)} 个文件，{vec_total} 个向量）")

        elif _kb.file_exists(args.name, args.target):
            # 删除单个文件
            deleted = _indexer.delete_vectors(args.name, args.target)
            _kb.remove_file(args.name, args.target)
            print(f"[OK] 已删除: {args.target}（移除了 {deleted} 个向量）")

        else:
            print(f"[ERROR] '{args.target}' 不存在于知识库 '{args.name}' 中")
            sys.exit(1)

    except KnowledgeBaseError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_reindex(args):
    try:
        _kb.ensure_exists(args.name)
        if not _kb.file_exists(args.name, args.filename):
            print(f"[ERROR] 文件 '{args.filename}' 不存在于知识库 '{args.name}' 中")
            sys.exit(1)
        print(f"[索引] 重新索引 '{args.filename}'...")
        count = _indexer.reindex_file(args.name, args.filename)
        print(f"[OK] 重新索引完成: {count} 个块")
    except (KnowledgeBaseError, FileNotFoundError) as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


def cmd_list(args):
    if args.name:
        try:
            items = _kb.list_files(args.name)
            if not items:
                print(f"知识库 '{args.name}' 为空")
                return
            print(f"\n知识库 '{args.name}' 中的内容:")
            print(f"{'='*50}")
            folders = [i for i in items if i["type"] == "folder"]
            files = [i for i in items if i["type"] == "file"]
            for f in folders:
                print(f"  📁 {f['name']:38s} {f['size_str']:>8s}")
            for f in files:
                print(f"  📄 {f['name']:38s} {f['size_str']:>8s}")
            print(f"{'='*50}")
            total_folders = len(folders)
            total_files = len(files)
            parts = []
            if total_folders:
                parts.append(f"{total_folders} 个文件夹")
            if total_files:
                parts.append(f"{total_files} 个文件")
            print(f"共 {'，'.join(parts)}")
        except KnowledgeBaseError as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
    else:
        kbs = _kb.list_all()
        if not kbs:
            print("暂无知识库")
            return
        print(f"\n知识库列表:")
        print(f"{'='*50}")
        for kb_name in kbs:
            items = _kb.list_files(kb_name)
            fcount = sum(1 for i in items if i["type"] == "file")
            dircount = sum(1 for i in items if i["type"] == "folder")
            summary = []
            if fcount:
                summary.append(f"{fcount} 文件")
            if dircount:
                summary.append(f"{dircount} 文件夹")
            summary_str = "，".join(summary) if summary else "空"
            print(f"  {kb_name:30s} ({summary_str})")
        print(f"{'='*50}")
        print(f"共 {len(kbs)} 个知识库")


def _print_index_results(results: dict):
    """打印索引结果汇总"""
    ok = sum(1 for v in results.values() if isinstance(v, int))
    err = sum(1 for v in results.values() if isinstance(v, str))
    total_chunks = sum(v for v in results.values() if isinstance(v, int))
    print(f"[OK] 索引完成: {ok} 个文件，{total_chunks} 个块")
    if err:
        print(f"[警告] {err} 个文件索引失败:")
        for name, err_msg in results.items():
            if isinstance(err_msg, str):
                print(f"       - {name}: {err_msg}")


def main():
    parser = argparse.ArgumentParser(
        description="RAG V — 知识库管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m app.modules.kb_manager.cli kb create my-docs
  python -m app.modules.kb_manager.cli kb upload my-docs report.pdf
  python -m app.modules.kb_manager.cli kb upload my-docs ./docs/
  python -m app.modules.kb_manager.cli kb index my-docs report.pdf
  python -m app.modules.kb_manager.cli kb index my-docs ./docs/
  python -m app.modules.kb_manager.cli kb index my-docs --all
  python -m app.modules.kb_manager.cli kb upload-and-index my-docs report.pdf
  python -m app.modules.kb_manager.cli kb delete my-docs               # 删知识库
  python -m app.modules.kb_manager.cli kb delete my-docs report.pdf    # 删文件
  python -m app.modules.kb_manager.cli kb delete my-docs my-folder     # 删文件夹
  python -m app.modules.kb_manager.cli kb reindex my-docs report.pdf
  python -m app.modules.kb_manager.cli kb list my-docs
  python -m app.modules.kb_manager.cli kb list
        """,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # kb 命令组
    kb_parser = sub.add_parser("kb", help="知识库管理")
    kb_sub = kb_parser.add_subparsers(dest="action", required=True)

    # kb create
    p_create = kb_sub.add_parser("create", help="创建知识库")
    p_create.add_argument("name", help="知识库名称")
    p_create.set_defaults(func=cmd_create)

    # kb upload（仅复制，不索引）
    p_upload = kb_sub.add_parser("upload", help="上传文件或文件夹（不自动索引）")
    p_upload.add_argument("name", help="知识库名称")
    p_upload.add_argument("path", help="文件或文件夹路径")
    p_upload.set_defaults(func=cmd_upload)

    # kb index（新增）
    p_index = kb_sub.add_parser("index", help="索引文件/文件夹/全部")
    p_index.add_argument("name", help="知识库名称")
    p_index.add_argument("target", nargs="?", default=None, help="文件名或文件夹名")
    p_index.add_argument("--all", action="store_true", help="索引所有文件")
    p_index.set_defaults(func=cmd_index)

    # kb upload-and-index（新增）
    p_ui = kb_sub.add_parser("upload-and-index", help="上传并索引（一步完成）")
    p_ui.add_argument("name", help="知识库名称")
    p_ui.add_argument("path", help="文件或文件夹路径")
    p_ui.set_defaults(func=cmd_upload_and_index)

    # kb delete
    p_delete = kb_sub.add_parser("delete", help="删除知识库、文件或文件夹")
    p_delete.add_argument("name", help="知识库名称")
    p_delete.add_argument("target", nargs="?", default=None,
                          help="文件名或文件夹名（省略时删除整个知识库）")
    p_delete.set_defaults(func=cmd_delete)

    # kb reindex
    p_reindex = kb_sub.add_parser("reindex", help="重新索引文件")
    p_reindex.add_argument("name", help="知识库名称")
    p_reindex.add_argument("filename", help="文件名")
    p_reindex.set_defaults(func=cmd_reindex)

    # kb list
    p_list = kb_sub.add_parser("list", help="列出知识库或内容")
    p_list.add_argument("name", nargs="?", default=None, help="知识库名称（可选）")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

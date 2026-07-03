"""
KnowledgeBase — 知识库管理核心类。

每个知识库在 `kb/<name>/` 下自包含：
    files/      上传的文件副本（同名保存）
    vector_db/  ChromaDB 持久化目录
"""

import json
import os
import shutil

from config.settings import KB_ROOT

# 索引时跳过的临时文件
IGNORED_FILES = {".DS_Store", "Thumbs.db", "desktop.ini", "._*"}
IGNORED_DIRS = {"__pycache__", ".git", ".svn"}


class KnowledgeBaseError(Exception):
    """知识库操作异常基类"""
    pass


class KnowledgeBase:
    """知识库管理"""

    def __init__(self, root: str = KB_ROOT):
        self.root = root

    # ── 路径 ─────────────────────────────────

    def kb_path(self, name: str) -> str:
        return os.path.join(self.root, name)

    def files_path(self, name: str) -> str:
        return os.path.join(self.root, name, "files")

    def vector_db_path(self, name: str) -> str:
        return os.path.join(self.root, name, "vector_db")

    # ── 索引状态持久化 ──────────────────────

    def _index_status_path(self, name: str) -> str:
        return os.path.join(self.root, name, ".index_status.json")

    def _load_index_status(self, name: str) -> dict:
        path = self._index_status_path(name)
        if not os.path.isfile(path):
            return {"files": {}}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"files": {}}

    def _save_index_status(self, name: str, data: dict):
        path = self._index_status_path(name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def set_file_status(self, name: str, filename: str, status: str, chunks: int | None = None):
        """设置文件的索引状态。status: 'pending' | 'indexed'"""
        data = self._load_index_status(name)
        entry = data["files"].get(filename, {})
        entry["status"] = status
        if chunks is not None:
            entry["chunks"] = chunks
        if status == "indexed":
            import datetime
            entry["indexed_at"] = datetime.datetime.now().isoformat()
        elif status == "pending":
            entry["chunks"] = None
            entry["indexed_at"] = None
        data["files"][filename] = entry
        self._save_index_status(name, data)

    def get_file_status(self, name: str, filename: str) -> dict:
        """获取文件索引状态。返回 {"status": str, "chunks": int|null, "indexed_at": str|null}"""
        data = self._load_index_status(name)
        return data["files"].get(filename, {"status": "pending", "chunks": None, "indexed_at": None})

    def remove_file_status(self, name: str, filename: str):
        """删除文件的索引状态条目。"""
        data = self._load_index_status(name)
        data["files"].pop(filename, None)
        self._save_index_status(name, data)

    # ── CRUD ────────────────────────────────

    def create(self, name: str) -> str:
        """创建知识库（目录结构）。返回知识库路径。"""
        path = self.kb_path(name)
        if os.path.exists(path):
            raise KnowledgeBaseError(f"知识库 '{name}' 已存在")
        os.makedirs(self.files_path(name), exist_ok=True)
        os.makedirs(self.vector_db_path(name), exist_ok=True)
        # 创建空的索引状态文件，确保后续操作可直接读写
        self._save_index_status(name, {"files": {}})
        return path

    def destroy(self, name: str):
        """删除整个知识库（递归删除所有文件、向量库）。"""
        path = self.kb_path(name)
        if not os.path.exists(path):
            raise KnowledgeBaseError(f"知识库 '{name}' 不存在")
        shutil.rmtree(path)

    def exists(self, name: str) -> bool:
        return os.path.isdir(self.kb_path(name))

    def ensure_exists(self, name: str):
        if not self.exists(name):
            raise KnowledgeBaseError(f"知识库 '{name}' 不存在")

    def list_all(self) -> list[str]:
        """列出所有知识库名称"""
        if not os.path.isdir(self.root):
            return []
        return sorted([
            d for d in os.listdir(self.root)
            if os.path.isdir(os.path.join(self.root, d))
        ])

    def list_files(self, name: str) -> list[dict]:
        """列出知识库中的文件和子目录"""
        self.ensure_exists(name)
        fdir = self.files_path(name)
        if not os.path.isdir(fdir):
            return []
        result = []
        for f in sorted(os.listdir(fdir)):
            fpath = os.path.join(fdir, f)
            if os.path.isfile(fpath):
                size = os.path.getsize(fpath)
                result.append({
                    "name": f, "size": size,
                    "size_str": _fmt_size(size), "type": "file",
                })
            elif os.path.isdir(fpath):
                count = _count_files(fpath)
                result.append({
                    "name": f, "type": "folder",
                    "files": count, "size_str": f"{count} files",
                })
        return result

    def file_path(self, name: str, filename: str) -> str:
        """文件或文件夹的完整路径（自动规范化路径分隔符）"""
        return os.path.normpath(os.path.join(self.files_path(name), filename))

    def file_exists(self, name: str, filename: str) -> bool:
        return os.path.isfile(self.file_path(name, filename))

    def folder_exists(self, name: str, folder_name: str) -> bool:
        return os.path.isdir(self.file_path(name, folder_name))

    # ── 文件操作 ────────────────────────────

    def copy_file(self, name: str, source_path: str) -> str:
        """复制文件到知识库（同名保存）。返回目标路径。"""
        self.ensure_exists(name)
        if not os.path.isfile(source_path):
            raise KnowledgeBaseError(f"文件不存在: {source_path}")
        filename = os.path.basename(source_path)
        dest_name = self._unique_filename(name, filename)
        dest = self.file_path(name, dest_name)
        shutil.copy2(source_path, dest)
        self.set_file_status(name, dest_name, "pending")
        return dest

    def remove_file(self, name: str, filename: str):
        """删除知识库中的文件副本"""
        self.ensure_exists(name)
        fpath = self.file_path(name, filename)
        if not os.path.isfile(fpath):
            raise KnowledgeBaseError(
                f"文件 '{filename}' 不存在于知识库 '{name}' 中"
            )
        os.remove(fpath)

    def _unique_filename(self, name: str, filename: str) -> str:
        """生成 files/ 中不重复的文件名，同名时加 _1, _2 后缀。"""
        fdir = self.files_path(name)
        if not os.path.exists(os.path.join(fdir, filename)):
            return filename
        base, ext = os.path.splitext(filename)
        i = 1
        while True:
            candidate = f"{base}_{i}{ext}"
            if not os.path.exists(os.path.join(fdir, candidate)):
                return candidate
            i += 1

    # ── 文件夹操作 ──────────────────────────

    def upload_folder(self, name: str, source_dir: str) -> list[str]:
        """
        将文件夹递归复制到知识库，所有文件平铺到 files/ 根目录。
        同名文件自动重命名：file.pdf → file_1.pdf。返回复制的文件名列表。
        """
        self.ensure_exists(name)
        if not os.path.isdir(source_dir):
            raise KnowledgeBaseError(f"目录不存在: {source_dir}")

        copied = []
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for f in files:
                if f in IGNORED_FILES or f.startswith("._"):
                    continue
                src = os.path.join(root, f)
                dest_name = self._unique_filename(name, f)
                shutil.copy2(src, self.file_path(name, dest_name))
                self.set_file_status(name, dest_name, "pending")
                copied.append(dest_name)

        return copied

    def list_folder_files(self, name: str, folder_name: str) -> list[str]:
        """
        递归列出文件夹中所有文件（相对路径）。
        用于索引和删除时的文件列表。
        """
        fdir = os.path.join(self.files_path(name), folder_name)
        if not os.path.isdir(fdir):
            return []
        result = []
        for root, dirs, files in os.walk(fdir):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
            for f in files:
                if f in IGNORED_FILES or f.startswith("._"):
                    continue
                full = os.path.join(root, f)
                rel = os.path.relpath(full, self.files_path(name))
                result.append(rel.replace("\\", "/"))
        return result

    def delete_file(self, name: str, filename: str):
        """删除知识库中的单个文件。"""
        self.ensure_exists(name)
        fpath = self.file_path(name, filename)
        if not os.path.isfile(fpath):
            raise KnowledgeBaseError(f"文件 '{filename}' 不存在")
        os.remove(fpath)
        # 清理索引状态和向量
        self.remove_file_status(name, filename)
        from app.modules.kb_manager.indexer import Indexer
        Indexer().delete_vectors(name, filename)

    def delete_folder(self, name: str, folder_name: str) -> list[str]:
        """
        删除知识库中的文件夹及其所有文件。
        返回被删除的文件列表（相对路径）。
        """
        self.ensure_exists(name)
        fdir = os.path.join(self.files_path(name), folder_name)
        if not os.path.isdir(fdir):
            raise KnowledgeBaseError(
                f"文件夹 '{folder_name}' 不存在于知识库 '{name}' 中"
            )

        files = self.list_folder_files(name, folder_name)
        for f in files:
            self.remove_file_status(name, f)
        shutil.rmtree(fdir)
        return files


def _count_files(directory: str) -> int:
    """递归统计文件数（不包含忽略文件）"""
    count = 0
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for f in files:
            if f not in IGNORED_FILES and not f.startswith("._"):
                count += 1
    return count


def _fmt_size(size: int) -> str:
    if size < 1024:
        return f"{size}B"
    elif size < 1024 ** 2:
        return f"{size / 1024:.1f}KB"
    else:
        return f"{size / 1024 ** 2:.1f}MB"

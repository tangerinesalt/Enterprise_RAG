"""
KnowledgeBase — 知识库管理核心类。

每个知识库在 `kb/<name>/` 下自包含：
    files/      上传的文件副本（同名保存）
    vector_db/  ChromaDB 持久化目录
"""

import json
import os
import shutil

from app.utils.storage_paths import basename_then_validate, child_path, resolve_under_root, validate_relative_path
from config.settings import KB_ROOT

# 索引时跳过的临时文件
IGNORED_FILES = {".DS_Store", "Thumbs.db", "desktop.ini", "._*"}
IGNORED_DIRS = {"__pycache__", ".git", ".svn"}


class KnowledgeBaseError(Exception):
    """知识库操作异常基类"""


class KnowledgeBasePathError(KnowledgeBaseError):
    """知识库路径或名称不合法"""


class KnowledgeBase:
    """知识库管理"""

    def __init__(self, root: str = KB_ROOT):
        self.root = os.path.abspath(root)

    def _wrap_path_error(self, exc: ValueError) -> KnowledgeBasePathError:
        return KnowledgeBasePathError(str(exc))

    def _normalize_file_ref(self, filename: str, label: str = "file path") -> str:
        try:
            return validate_relative_path(filename, label)
        except ValueError as exc:
            raise self._wrap_path_error(exc) from exc

    def validate_upload_name(self, filename: str) -> str:
        try:
            return basename_then_validate(filename, "filename")
        except ValueError as exc:
            raise self._wrap_path_error(exc) from exc

    # Path helpers

    def kb_path(self, name: str) -> str:
        try:
            return child_path(self.root, name, "knowledge base name")
        except ValueError as exc:
            raise self._wrap_path_error(exc) from exc

    def files_path(self, name: str) -> str:
        return os.path.join(self.kb_path(name), "files")

    def vector_db_path(self, name: str) -> str:
        return os.path.join(self.kb_path(name), "vector_db")

    # Index status persistence

    def _index_status_path(self, name: str) -> str:
        return os.path.join(self.kb_path(name), ".index_status.json")

    def _default_index_status(self) -> dict:
        return {"files": {}, "corpus_version": 0}

    def _load_index_status(self, name: str) -> dict:
        path = self._index_status_path(name)
        if not os.path.isfile(path):
            return self._default_index_status()
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            return self._default_index_status()

        if "files" not in data:
            data["files"] = {}
        if "corpus_version" not in data:
            data["corpus_version"] = 0
        return data

    def _save_index_status(self, name: str, data: dict):
        payload = dict(data)
        if "files" not in payload:
            payload["files"] = {}
        if "corpus_version" not in payload:
            payload["corpus_version"] = 0

        path = self._index_status_path(name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def set_file_status(self, name: str, filename: str, status: str, chunks: int | None = None):
        normalized = self._normalize_file_ref(filename)
        data = self._load_index_status(name)
        entry = data["files"].get(normalized, {})
        entry["status"] = status
        if chunks is not None:
            entry["chunks"] = chunks
        if status == "indexed":
            import datetime

            entry["indexed_at"] = datetime.datetime.now().isoformat()
        elif status == "pending":
            entry["chunks"] = None
            entry["indexed_at"] = None
        data["files"][normalized] = entry
        self._save_index_status(name, data)

    def get_file_status(self, name: str, filename: str) -> dict:
        normalized = self._normalize_file_ref(filename)
        data = self._load_index_status(name)
        return data["files"].get(normalized, {"status": "pending", "chunks": None, "indexed_at": None})

    def remove_file_status(self, name: str, filename: str):
        normalized = self._normalize_file_ref(filename)
        data = self._load_index_status(name)
        data["files"].pop(normalized, None)
        self._save_index_status(name, data)

    def get_corpus_version(self, name: str) -> int:
        return int(self._load_index_status(name).get("corpus_version", 0))

    def bump_corpus_version(self, name: str) -> int:
        data = self._load_index_status(name)
        data["corpus_version"] = int(data.get("corpus_version", 0)) + 1
        self._save_index_status(name, data)
        return data["corpus_version"]

    # CRUD

    def create(self, name: str) -> str:
        path = self.kb_path(name)
        if os.path.exists(path):
            raise KnowledgeBaseError(f"知识库 '{name}' 已存在")
        os.makedirs(self.files_path(name), exist_ok=True)
        os.makedirs(self.vector_db_path(name), exist_ok=True)
        self._save_index_status(name, self._default_index_status())
        return path

    def destroy(self, name: str):
        path = self.kb_path(name)
        if not os.path.exists(path):
            raise KnowledgeBaseError(f"知识库 '{name}' 不存在")
        shutil.rmtree(path)

    def exists(self, name: str) -> bool:
        try:
            path = self.kb_path(name)
        except KnowledgeBasePathError:
            return False
        return os.path.isdir(path)

    def ensure_exists(self, name: str):
        path = self.kb_path(name)
        if not os.path.isdir(path):
            raise KnowledgeBaseError(f"知识库 '{name}' 不存在")

    def list_all(self) -> list[str]:
        if not os.path.isdir(self.root):
            return []
        return sorted(
            [entry for entry in os.listdir(self.root) if os.path.isdir(os.path.join(self.root, entry))]
        )

    def list_files(self, name: str) -> list[dict]:
        self.ensure_exists(name)
        files_dir = self.files_path(name)
        if not os.path.isdir(files_dir):
            return []

        result = []
        for entry in sorted(os.listdir(files_dir)):
            entry_path = os.path.join(files_dir, entry)
            if os.path.isfile(entry_path):
                size = os.path.getsize(entry_path)
                result.append({"name": entry, "size": size, "size_str": _fmt_size(size), "type": "file"})
            elif os.path.isdir(entry_path):
                count = _count_files(entry_path)
                result.append({"name": entry, "type": "folder", "files": count, "size_str": f"{count} files"})
        return result

    def file_path(self, name: str, filename: str) -> str:
        normalized = self._normalize_file_ref(filename)
        try:
            return resolve_under_root(self.files_path(name), normalized, "file path")
        except ValueError as exc:
            raise self._wrap_path_error(exc) from exc

    def file_exists(self, name: str, filename: str) -> bool:
        return os.path.isfile(self.file_path(name, filename))

    def folder_exists(self, name: str, folder_name: str) -> bool:
        return os.path.isdir(self.file_path(name, folder_name))

    # File operations

    def copy_file(self, name: str, source_path: str) -> str:
        self.ensure_exists(name)
        if not os.path.isfile(source_path):
            raise KnowledgeBaseError(f"文件不存在: {source_path}")
        filename = self.validate_upload_name(os.path.basename(source_path))
        dest_name = self._unique_filename(name, filename)
        dest = self.file_path(name, dest_name)
        shutil.copy2(source_path, dest)
        self.set_file_status(name, dest_name, "pending")
        return dest

    def remove_file(self, name: str, filename: str):
        self.ensure_exists(name)
        normalized = self._normalize_file_ref(filename)
        path = self.file_path(name, normalized)
        if not os.path.isfile(path):
            raise KnowledgeBaseError(f"文件 '{filename}' 不存在于知识库 '{name}' 中")
        os.remove(path)

    def _unique_filename(self, name: str, filename: str) -> str:
        filename = self.validate_upload_name(filename)
        files_dir = self.files_path(name)
        if not os.path.exists(os.path.join(files_dir, filename)):
            return filename

        base, ext = os.path.splitext(filename)
        index = 1
        while True:
            candidate = f"{base}_{index}{ext}"
            if not os.path.exists(os.path.join(files_dir, candidate)):
                return candidate
            index += 1

    # Folder operations

    def upload_folder(self, name: str, source_dir: str) -> list[str]:
        self.ensure_exists(name)
        if not os.path.isdir(source_dir):
            raise KnowledgeBaseError(f"目录不存在: {source_dir}")

        copied = []
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [entry for entry in dirs if entry not in IGNORED_DIRS]
            for filename in files:
                if filename in IGNORED_FILES or filename.startswith("._"):
                    continue
                source = os.path.join(root, filename)
                dest_name = self._unique_filename(name, filename)
                shutil.copy2(source, self.file_path(name, dest_name))
                self.set_file_status(name, dest_name, "pending")
                copied.append(dest_name)
        return copied

    def list_folder_files(self, name: str, folder_name: str) -> list[str]:
        folder_path = self.file_path(name, folder_name)
        if not os.path.isdir(folder_path):
            return []

        result = []
        for root, dirs, files in os.walk(folder_path):
            dirs[:] = [entry for entry in dirs if entry not in IGNORED_DIRS]
            for filename in files:
                if filename in IGNORED_FILES or filename.startswith("._"):
                    continue
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, self.files_path(name)).replace("\\", "/")
                result.append(rel_path)
        return result

    def delete_file(self, name: str, filename: str):
        self.ensure_exists(name)
        normalized = self._normalize_file_ref(filename)
        file_path = self.file_path(name, normalized)
        if not os.path.isfile(file_path):
            raise KnowledgeBaseError(f"文件 '{filename}' 不存在")
        os.remove(file_path)
        self.remove_file_status(name, normalized)
        from app.modules.kb_manager.indexer import Indexer

        Indexer().delete_vectors(name, normalized)

    def delete_folder(self, name: str, folder_name: str) -> list[str]:
        self.ensure_exists(name)
        folder_path = self.file_path(name, folder_name)
        if not os.path.isdir(folder_path):
            raise KnowledgeBaseError(f"文件夹 '{folder_name}' 不存在于知识库 '{name}' 中")

        files = self.list_folder_files(name, folder_name)
        for filename in files:
            self.remove_file_status(name, filename)
        shutil.rmtree(folder_path)
        return files


def _count_files(directory: str) -> int:
    count = 0
    for _root, dirs, files in os.walk(directory):
        dirs[:] = [entry for entry in dirs if entry not in IGNORED_DIRS]
        for filename in files:
            if filename not in IGNORED_FILES and not filename.startswith("._"):
                count += 1
    return count


def _fmt_size(size: int) -> str:
    if size < 1024:
        return f"{size}B"
    if size < 1024**2:
        return f"{size / 1024:.1f}KB"
    return f"{size / 1024**2:.1f}MB"

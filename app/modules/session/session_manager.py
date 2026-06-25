"""
SessionManager — 会话管理核心类。

每个会话在 `sessions/<name>/` 下自包含：
    config.json      会话配置（kb_name, active_chat）
    chats/           SimpleChatStore JSON 文件（每条对话独立）
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

import chromadb
from llama_index.core import (
    VectorStoreIndex, Settings, StorageContext,
)
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.vector_stores.chroma import ChromaVectorStore

from config.settings import KB_ROOT, EMBED_MODEL, LLM_MODEL
from config.init import init_models
from app.modules.kb_manager import KnowledgeBase

# 会话根目录
SESSION_ROOT = str((Path(__file__).resolve().parent.parent.parent.parent / "sessions").resolve())

_kb = KnowledgeBase()


class SessionError(Exception):
    pass


class SessionManager:
    """会话管理"""

    # ── 路径 ─────────────────────────────────

    def session_path(self, name: str) -> str:
        return os.path.join(SESSION_ROOT, name)

    def config_path(self, name: str) -> str:
        return os.path.join(self.session_path(name), "config.json")

    def chats_dir(self, name: str) -> str:
        return os.path.join(self.session_path(name), "chats")

    # ── 会话 CRUD ───────────────────────────

    def create(self, name: str) -> str:
        path = self.session_path(name)
        if os.path.exists(path):
            raise SessionError(f"会话 '{name}' 已存在")
        os.makedirs(self.chats_dir(name), exist_ok=True)
        self._save_config(name, {"kb_name": None, "active_chat": None})
        return path

    def delete(self, name: str, chat_file: str = None):
        if chat_file:
            # 删除单条聊天
            chat_path = os.path.join(self.chats_dir(name), chat_file)
            if not os.path.isfile(chat_path):
                raise SessionError(f"聊天文件 '{chat_file}' 不存在")
            os.remove(chat_path)
            # 如果删掉的是当前 active_chat，清除
            config = self._load_config(name)
            if config.get("active_chat") == chat_file:
                config["active_chat"] = None
                self._save_config(name, config)
        else:
            # 删除整个会话
            path = self.session_path(name)
            if not os.path.exists(path):
                raise SessionError(f"会话 '{name}' 不存在")
            shutil.rmtree(path)

    def exists(self, name: str) -> bool:
        return os.path.isdir(self.session_path(name))

    def _ensure_exists(self, name: str):
        if not self.exists(name):
            raise SessionError(f"会话 '{name}' 不存在")

    # ── 绑定知识库 ─────────────────────────

    def bind(self, name: str, kb_name: str):
        self._ensure_exists(name)
        if not _kb.exists(kb_name):
            raise SessionError(f"知识库 '{kb_name}' 不存在")
        config = self._load_config(name)
        config["kb_name"] = kb_name
        self._save_config(name, config)

    def info(self, name: str) -> dict:
        self._ensure_exists(name)
        config = self._load_config(name)
        chats = self.list_chats(name)
        return {
            "name": name,
            "kb_name": config.get("kb_name"),
            "active_chat": config.get("active_chat"),
            "total_chats": len(chats),
            "chat_files": chats,
        }

    # ── 列表 ───────────────────────────────

    def list_all(self) -> list[dict]:
        if not os.path.isdir(SESSION_ROOT):
            return []
        result = []
        for d in sorted(os.listdir(SESSION_ROOT)):
            path = os.path.join(SESSION_ROOT, d)
            if os.path.isdir(path):
                config = self._load_config(d)
                chats = self.list_chats(d)
                result.append({
                    "name": d,
                    "kb_name": config.get("kb_name"),
                    "active_chat": config.get("active_chat"),
                    "total_chats": len(chats),
                })
        return result

    def list_chats(self, name: str) -> list[dict]:
        self._ensure_exists(name)
        cdir = self.chats_dir(name)
        if not os.path.isdir(cdir):
            return []
        config = self._load_config(name)
        active = config.get("active_chat")
        result = []
        for f in sorted(os.listdir(cdir)):
            if f.endswith(".json"):
                fpath = os.path.join(cdir, f)
                msg_count = self._count_chat_messages(fpath)
                result.append({
                    "file": f,
                    "is_active": f == active,
                    "messages": msg_count,
                    "size": os.path.getsize(fpath),
                })
        return result

    # ── 聊天管理 ───────────────────────────

    def new_chat(self, name: str) -> str:
        """新建聊天文件（设为 active_chat）。返回文件名。"""
        self._ensure_exists(name)
        filename = self._gen_chat_filename(name)
        # 创建空的 SimpleChatStore 并持久化
        store = SimpleChatStore()
        store.persist(os.path.join(self.chats_dir(name), filename))
        # 设为当前
        config = self._load_config(name)
        config["active_chat"] = filename
        self._save_config(name, config)
        return filename

    def select_chat(self, name: str, chat_file: str):
        """切换到指定的历史聊天文件。"""
        self._ensure_exists(name)
        chat_path = os.path.join(self.chats_dir(name), chat_file)
        if not os.path.isfile(chat_path):
            raise SessionError(f"聊天文件 '{chat_file}' 不存在")
        config = self._load_config(name)
        config["active_chat"] = chat_file
        self._save_config(name, config)

    # ── 获取聊天记录 ───────────────────────

    def get_messages(self, name: str, chat_file: str) -> list[dict]:
        """获取指定聊天文件的全部消息记录。"""
        self._ensure_exists(name)
        chat_path = os.path.join(self.chats_dir(name), chat_file)
        if not os.path.isfile(chat_path):
            raise SessionError(f"聊天文件 '{chat_file}' 不存在")

        store = SimpleChatStore.from_persist_path(chat_path)
        keys = store.get_keys()
        if not keys:
            return []

        messages = store.get_messages(keys[0])
        return [
            {
                "role": str(m.role),
                "content": m.content,
                "additional_kwargs": m.additional_kwargs,
            }
            for m in messages
        ]

    # ── 聊天核心 ───────────────────────────

    def chat(self, name: str, query: str, chat_file: str = None) -> dict:
        """
        聊天：检索绑定 KB → LLM 生成 → 持久化 → print。

        如果 chat_file 指定 → 继续该聊天
        如果 chat_file 未指定 → 自动新建聊天
        """
        self._ensure_exists(name)
        config = self._load_config(name)

        # 确定聊天文件
        if chat_file:
            # 使用指定的聊天
            chat_path = os.path.join(self.chats_dir(name), chat_file)
            if not os.path.isfile(chat_path):
                raise SessionError(f"聊天文件 '{chat_file}' 不存在")
        else:
            # 自动新建
            chat_file = self.new_chat(name)
            config = self._load_config(name)  # reload
            chat_path = os.path.join(self.chats_dir(name), chat_file)

        # 检查绑定的知识库
        kb_name = config.get("kb_name")
        if not kb_name:
            raise SessionError(f"会话 '{name}' 未绑定知识库")
        if not _kb.exists(kb_name):
            raise SessionError(f"知识库 '{kb_name}' 不存在")

        # 加载聊天历史
        store = SimpleChatStore.from_persist_path(chat_path)

        # 初始化模型
        init_models()

        # 加载 ChromaDB
        db = chromadb.PersistentClient(path=_kb.vector_db_path(kb_name))
        try:
            chroma_collection = db.get_collection("kb_index")
        except Exception:
            raise SessionError(f"知识库 '{kb_name}' 中未找到索引数据")

        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

        vector_count = chroma_collection.count()
        if vector_count == 0:
            raise SessionError(f"知识库 '{kb_name}' 中没有向量数据")

        # 追加用户消息
        store.add_message(name, ChatMessage(role=MessageRole.USER, content=query))

        # 检索 + 生成
        query_engine = index.as_query_engine(similarity_top_k=5)
        response = query_engine.query(query)

        # 提取来源
        sources = []
        if hasattr(response, "source_nodes") and response.source_nodes:
            for node in response.source_nodes:
                score = node.score if hasattr(node, "score") else None
                sources.append({
                    "text": node.text.strip()[:300],
                    "score": round(score, 4) if isinstance(score, float) else None,
                })

        answer = str(response)

        # 构造带来源的助手消息
        answer_with_sources = answer
        if sources:
            answer_with_sources += "\n\n---\n来源:\n"
            for i, s in enumerate(sources):
                answer_with_sources += f"\n[{i+1}] (相关度: {s['score']}) {s['text']}"

        store.add_message(
            name,
            ChatMessage(role=MessageRole.ASSISTANT, content=answer_with_sources),
        )

        # 持久化
        store.persist(chat_path)

        return {
            "query": query,
            "answer": answer,
            "sources": sources,
            "chat_file": chat_file,
            "chat_path": chat_path,
        }

    # ── 内部方法 ───────────────────────────

    def _load_config(self, name: str) -> dict:
        path = self.config_path(name)
        if not os.path.isfile(path):
            return {"kb_name": None, "active_chat": None}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_config(self, name: str, data: dict):
        os.makedirs(os.path.dirname(self.config_path(name)), exist_ok=True)
        with open(self.config_path(name), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _gen_chat_filename(self, name: str) -> str:
        """按时间生成文件名，处理冲突。"""
        base = datetime.now().strftime("%Y_%m_%d_%H_%M")
        cdir = self.chats_dir(name)
        os.makedirs(cdir, exist_ok=True)

        filename = f"{base}.json"
        if not os.path.isfile(os.path.join(cdir, filename)):
            return filename

        # 有冲突，加 _1, _2 ...
        i = 1
        while True:
            filename = f"{base}_{i}.json"
            if not os.path.isfile(os.path.join(cdir, filename)):
                return filename
            i += 1

    def _count_chat_messages(self, fpath: str) -> int:
        try:
            store = SimpleChatStore.from_persist_path(fpath)
            keys = store.get_keys()
            return sum(len(store.get_messages(k)) for k in keys)
        except Exception:
            return 0

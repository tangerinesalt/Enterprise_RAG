"""
SessionManager — 会话管理核心类。

每个会话在 `sessions/<name>/` 下自包含：
    config.json      会话配置（kb_name, active_chat）
    chats/           SimpleChatStore JSON 文件（每条对话独立）
"""

import os
import json
import shutil
from threading import Lock
from datetime import datetime
from pathlib import Path

import chromadb
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core import PromptTemplate
from llama_index.vector_stores.chroma import ChromaVectorStore

from config.init import init_models
from app.modules.kb_manager import KnowledgeBase
from app.modules.retrieval import build_retriever


# ── 中文分词器（用于 BM25）─────────────────
# 会话根目录
SESSION_ROOT = str((Path(__file__).resolve().parent.parent.parent.parent / "sessions").resolve())

_kb = KnowledgeBase()
_models_initialized = False
_models_lock = Lock()


def _ensure_models_initialized() -> bool:
    """Initialize LlamaIndex global models once per Python process."""
    global _models_initialized
    if _models_initialized:
        return False

    with _models_lock:
        if _models_initialized:
            return False
        init_models()
        _models_initialized = True
        return True


class SessionError(Exception):
    pass


class SessionManager:
    """会话管理"""

    # 检索参数默认值
    DEFAULT_TOP_K = 8
    DEFAULT_TOP_N = 5
    DEFAULT_RETRIEVER_MODE = "hybrid"
    DEFAULT_SYSTEM_PROMPT = ""

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
        self._save_config(name, {
            "kb_name": None,
            "active_chat": None,
            "top_k": self.DEFAULT_TOP_K,
            "top_n": self.DEFAULT_TOP_N,
            "retriever_mode": self.DEFAULT_RETRIEVER_MODE,
            "system_prompt": self.DEFAULT_SYSTEM_PROMPT,
        })
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
            "top_k": config.get("top_k", self.DEFAULT_TOP_K),
            "top_n": config.get("top_n", self.DEFAULT_TOP_N),
            "system_prompt": config.get("system_prompt", self.DEFAULT_SYSTEM_PROMPT),
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
                "role": m.role.value if hasattr(m.role, 'value') else str(m.role),
                "content": m.content,
                "additional_kwargs": m.additional_kwargs,
            }
            for m in messages
        ]

    # ── 流式聊天核心 ───────────────────────

    def chat_stream(self, name: str, query: str, chat_file: str = None):
        """
        流式聊天 Generator。

        逐 token 生成 SSE 事件 dict：
            {"type": "start",   "chat_file": "..."}
            {"type": "token",   "token": "..."}
            {"type": "sources", "sources": [...]}
            {"type": "done",    "chat_file": "..."}
            {"type": "error",   "message": "..."}
        """
        import time as _time
        _t = _time.time

        try:
            self._ensure_exists(name)
            config = self._load_config(name)

            # 确定聊天文件
            if chat_file:
                chat_path = os.path.join(self.chats_dir(name), chat_file)
                if not os.path.isfile(chat_path):
                    raise SessionError(f"聊天文件 '{chat_file}' 不存在")
            else:
                chat_file = self.new_chat(name)
                config = self._load_config(name)
                chat_path = os.path.join(self.chats_dir(name), chat_file)

            yield {"type": "start", "chat_file": chat_file}

            # 检查绑定的知识库
            kb_name = config.get("kb_name")
            if not kb_name:
                raise SessionError(f"会话 '{name}' 未绑定知识库")
            if not _kb.exists(kb_name):
                raise SessionError(f"知识库 '{kb_name}' 不存在")

            # 加载历史 + 初始化模型
            t0 = _t()
            store = SimpleChatStore.from_persist_path(chat_path)
            did_init = _ensure_models_initialized()
            init_state = "init" if did_init else "cached"
            print(f"[TIMING] load_history+models_{init_state}: {_t()-t0:.3f}s")

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

            # 流式检索 + 生成
            top_k = config.get("top_k", self.DEFAULT_TOP_K)
            top_n = config.get("top_n", self.DEFAULT_TOP_N)
            retriever_mode = config.get("retriever_mode", self.DEFAULT_RETRIEVER_MODE)
            reranker = SentenceTransformerRerank(
                model=r"C:\Users\tangerine\.rag_v\models\BAAI\bge-reranker-v2-m3",
                top_n=top_n,
            )
            retriever = build_retriever(index, kb_name, top_k=top_k, mode=retriever_mode)
            sp = config.get("system_prompt", "")
            query_engine = RetrieverQueryEngine.from_args(
                retriever=retriever, node_postprocessors=[reranker],
                text_qa_template=PromptTemplate(sp) if sp else None,
                streaming=True,
            )
            t0 = _t()
            response = query_engine.query(query)
            print(f"[TIMING] retrieval: {_t()-t0:.3f}s")

            answer_buf = []
            for chunk in response.response_gen:
                if chunk:
                    answer_buf.append(chunk)
                    yield {"type": "token", "token": chunk}
                    t0 = _t()

            answer = "".join(answer_buf)
            print(f"[TIMING] generation: {_t()-t0:.3f}s")

            # 提取来源
            sources = []
            if hasattr(response, "source_nodes") and response.source_nodes:
                for node in response.source_nodes:
                    score = node.score if hasattr(node, "score") else None
                    sources.append({
                        "text": node.text.strip(),
                        "score": round(float(score), 4) if score is not None else None,
                    })

            # 持久化
            store.add_message(
                name,
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=answer,
                    additional_kwargs={"sources": sources} if sources else None,
                ),
            )
            t0 = _t()
            store.persist(chat_path)
            print(f"[TIMING] persist: {_t()-t0:.3f}s")

            yield {"type": "sources", "sources": sources}
            yield {"type": "done", "chat_file": chat_file}

        except SessionError as e:
            yield {"type": "error", "message": str(e)}
        except Exception as e:
            print(f"\033[91m[ERROR] chat_stream: {e}\033[0m")
            yield {"type": "error", "message": f"内部错误: {e}"}

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

        # 阶段 1：加载历史 + 初始化模型
        import time as _time
        _t = _time.time
        t0 = _t()
        store = SimpleChatStore.from_persist_path(chat_path)
        did_init = _ensure_models_initialized()
        init_state = "init" if did_init else "cached"
        print(f"[TIMING] load_history+models_{init_state}: {_t()-t0:.3f}s")

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

        # 阶段 2：检索 + 生成
        t0 = _t()
        top_k = config.get("top_k", self.DEFAULT_TOP_K)
        top_n = config.get("top_n", self.DEFAULT_TOP_N)
        retriever_mode = config.get("retriever_mode", self.DEFAULT_RETRIEVER_MODE)
        retriever = build_retriever(index, kb_name, top_k=top_k, mode=retriever_mode)
        reranker = SentenceTransformerRerank(
            model=r"C:\Users\tangerine\.rag_v\models\BAAI\bge-reranker-v2-m3",
            top_n=top_n,
        )
        sp = config.get("system_prompt", "")
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever, node_postprocessors=[reranker],
            text_qa_template=PromptTemplate(sp) if sp else None,
        )
        response = query_engine.query(query)
        print(f"[TIMING] retrieval+generation: {_t()-t0:.3f}s")

        # 提取来源
        sources = []
        if hasattr(response, "source_nodes") and response.source_nodes:
            for node in response.source_nodes:
                score = node.score if hasattr(node, "score") else None
                sources.append({
                    "text": node.text.strip(),
                    "score": round(float(score), 4) if score is not None else None,
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

        # 阶段 3：持久化
        t0 = _t()
        store.persist(chat_path)
        print(f"[TIMING] persist: {_t()-t0:.3f}s")

        return {
            "query": query,
            "answer": answer,
            "sources": sources,
            "chat_file": chat_file,
            "chat_path": chat_path,
        }

    # ── 检索参数管理 ─────────────────────────

    def get_config(self, name: str) -> dict:
        """获取会话完整配置（含 top_k / top_n）。"""
        self._ensure_exists(name)
        return self._load_config(name)

    def update_config(self, name: str, **kwargs) -> dict:
        """更新会话配置参数。校验通过后持久化，返回完整配置。"""
        self._ensure_exists(name)
        cfg = self._load_config(name)

        for key, value in kwargs.items():
            if key in ("top_k", "top_n"):
                if not isinstance(value, int) or value < 1:
                    raise SessionError(f"{key} MUST be >= 1, got {value}")
                cfg[key] = value
            elif key == "retriever_mode":
                if value not in ("hybrid", "vector-only"):
                    raise SessionError(
                        f"retriever_mode MUST be 'hybrid' or 'vector-only', got '{value}'")
                cfg[key] = value
            elif key == "system_prompt":
                if not isinstance(value, str):
                    raise SessionError(f"system_prompt MUST be a string")
                cfg[key] = value
            else:
                raise SessionError(f"不支持的配置项: {key}")

        self._save_config(name, cfg)
        return cfg

    # ── 内部方法 ───────────────────────────

    def _load_config(self, name: str) -> dict:
        path = self.config_path(name)
        if not os.path.isfile(path):
            return {"kb_name": None, "active_chat": None,
                    "top_k": self.DEFAULT_TOP_K, "top_n": self.DEFAULT_TOP_N,
                    "retriever_mode": self.DEFAULT_RETRIEVER_MODE,
                    "system_prompt": self.DEFAULT_SYSTEM_PROMPT}
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        # 兼容旧 config：缺失字段用默认值补全
        if "top_k" not in cfg:
            cfg["top_k"] = self.DEFAULT_TOP_K
        if "top_n" not in cfg:
            cfg["top_n"] = self.DEFAULT_TOP_N
        if "retriever_mode" not in cfg:
            cfg["retriever_mode"] = self.DEFAULT_RETRIEVER_MODE
        if "system_prompt" not in cfg:
            cfg["system_prompt"] = self.DEFAULT_SYSTEM_PROMPT
        return cfg

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

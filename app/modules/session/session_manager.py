"""
Session manager for session-scoped chats and retrieval config.
"""

import json
import os
import shutil
import tempfile
import time
from datetime import datetime
from pathlib import Path
from threading import Lock, RLock

import chromadb
from llama_index.core import PromptTemplate, VectorStoreIndex
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.core.postprocessor import SentenceTransformerRerank, SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.vector_stores.chroma import ChromaVectorStore

from app.modules.kb_manager import KnowledgeBase
from app.modules.retrieval import build_retriever
from app.utils.logging import get_logger
from config.init import init_models

SESSION_ROOT = str((Path(__file__).resolve().parent.parent.parent.parent / "sessions").resolve())

logger = get_logger(__name__)
_kb = KnowledgeBase()
_models_initialized = False
_models_lock = Lock()
_session_config_locks: dict[str, RLock] = {}
_session_config_locks_guard = Lock()
_chat_file_locks: dict[tuple[str, str], RLock] = {}
_chat_file_locks_guard = Lock()
_reranker_instances: dict[int, SentenceTransformerRerank] = {}
_reranker_lock = Lock()


def _get_reranker(top_n: int = 5) -> SentenceTransformerRerank:
    """Cache SentenceTransformerRerank per top_n value."""
    reranker = _reranker_instances.get(top_n)
    if reranker is not None:
        return reranker

    with _reranker_lock:
        reranker = _reranker_instances.get(top_n)
        if reranker is not None:
            return reranker

        reranker = SentenceTransformerRerank(
            model=r"C:\Users\tangerine\.rag_v\models\BAAI\bge-reranker-v2-m3",
            top_n=top_n,
        )
        _reranker_instances[top_n] = reranker
        return reranker


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
    DEFAULT_TOP_K = 8
    DEFAULT_TOP_N = 5
    DEFAULT_RETRIEVER_MODE = "hybrid"
    RETRIEVAL_HINT_TEXT = (
        "补充：本次最终保留来源已达到当前上限 {cap} 条，且尾部来源仍有一定相关性。"
        "如需让结果更集中或更全面，可适时调整检索参数，例如 top_k 或 top_n。"
    )
    DEFAULT_SYSTEM_PROMPT = (
        "你是一个知识库问答助手。请严格遵循以下规则：\n\n"
        "1. 根据提供的上下文内容回答，不要编造不存在的条款。\n"
        "2. 如果上下文包含不同版本的内容，以最新版本为准。\n"
        "3. 回答需准确、简洁、有逻辑。分点说明时使用编号。\n"
        "4. 如果上下文信息不足以回答，明确说明：根据提供的内容无法确定，不要猜测。\n"
        "5. 回答基于原文，不要添加个人建议或主观评价。\n"
        "6. 如果问题在不同情形下会导致结果不同，必须在回答中明确说明差异条件、适用范围和对应结论，不能把依赖情形的答案说成唯一结论。\n\n"
        "上下文内容：\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "问题：{query_str}\n"
        "回答："
    )
    CONTEXT_SUFFIX = (
        "\n\n上下文内容：\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "问题：{query_str}\n"
        "回答："
    )

    def session_path(self, name: str) -> str:
        return os.path.join(SESSION_ROOT, name)

    def config_path(self, name: str) -> str:
        return os.path.join(self.session_path(name), "config.json")

    def chats_dir(self, name: str) -> str:
        return os.path.join(self.session_path(name), "chats")

    def _session_config_lock(self, name: str) -> RLock:
        with _session_config_locks_guard:
            lock = _session_config_locks.get(name)
            if lock is None:
                lock = RLock()
                _session_config_locks[name] = lock
            return lock

    def _chat_file_lock(self, name: str, chat_file: str) -> RLock:
        key = (name, chat_file)
        with _chat_file_locks_guard:
            lock = _chat_file_locks.get(key)
            if lock is None:
                lock = RLock()
                _chat_file_locks[key] = lock
            return lock

    def create(self, name: str) -> str:
        with self._session_config_lock(name):
            path = self.session_path(name)
            if os.path.exists(path):
                raise SessionError(f"会话 '{name}' 已存在")
            os.makedirs(self.chats_dir(name), exist_ok=True)
            self._save_config(
                name,
                {
                    "kb_name": None,
                    "active_chat": None,
                    "top_k": self.DEFAULT_TOP_K,
                    "top_n": self.DEFAULT_TOP_N,
                    "retriever_mode": self.DEFAULT_RETRIEVER_MODE,
                    "system_prompt": self.DEFAULT_SYSTEM_PROMPT,
                    "chat_previews": {},
                },
            )
            return path

    def delete(self, name: str, chat_file: str = None):
        with self._session_config_lock(name):
            if chat_file:
                self._ensure_exists(name)
                chat_path = os.path.join(self.chats_dir(name), chat_file)
                if not os.path.isfile(chat_path):
                    raise SessionError(f"聊天文件 '{chat_file}' 不存在")
                with self._chat_file_lock(name, chat_file):
                    os.remove(chat_path)

                config = self._load_config(name)
                if config.get("active_chat") == chat_file:
                    config["active_chat"] = None
                previews = dict(config.get("chat_previews", {}))
                previews.pop(chat_file, None)
                config["chat_previews"] = previews
                self._save_config(name, config)
                return

            path = self.session_path(name)
            if not os.path.exists(path):
                raise SessionError(f"会话 '{name}' 不存在")
            shutil.rmtree(path)

    def exists(self, name: str) -> bool:
        return os.path.isdir(self.session_path(name))

    def _ensure_exists(self, name: str):
        if not self.exists(name):
            raise SessionError(f"会话 '{name}' 不存在")

    def bind(self, name: str, kb_name: str):
        with self._session_config_lock(name):
            self._ensure_exists(name)
            if not _kb.exists(kb_name):
                raise SessionError(f"知识库 '{kb_name}' 不存在")
            config = self._load_config(name)
            config["kb_name"] = kb_name
            self._save_config(name, config)

    def info(self, name: str) -> dict:
        self._ensure_exists(name)
        with self._session_config_lock(name):
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

    def list_all(self) -> list[dict]:
        if not os.path.isdir(SESSION_ROOT):
            return []

        result = []
        for entry in sorted(os.listdir(SESSION_ROOT)):
            path = os.path.join(SESSION_ROOT, entry)
            if not os.path.isdir(path):
                continue
            config = self._load_config(entry)
            cdir = self.chats_dir(entry)
            total_chats = len([f for f in os.listdir(cdir) if f.endswith(".json")]) if os.path.isdir(cdir) else 0
            result.append(
                {
                    "name": entry,
                    "kb_name": config.get("kb_name"),
                    "active_chat": config.get("active_chat"),
                    "total_chats": total_chats,
                }
            )
        return result

    def list_chats(self, name: str) -> list[dict]:
        self._ensure_exists(name)
        cdir = self.chats_dir(name)
        if not os.path.isdir(cdir):
            return []

        with self._session_config_lock(name):
            config = self._load_config(name)
            active = config.get("active_chat")
            previews = dict(config.get("chat_previews", {}))

        result = []
        for filename in sorted(os.listdir(cdir)):
            if filename.endswith(".json"):
                result.append(
                    {
                        "file": filename,
                        "is_active": filename == active,
                        "preview": previews.get(filename),
                    }
                )
        return result

    def new_chat(self, name: str) -> str:
        with self._session_config_lock(name):
            self._ensure_exists(name)
            config = self._load_config(name)
            return self._create_chat_file_locked(name, config)

    def select_chat(self, name: str, chat_file: str):
        with self._session_config_lock(name):
            self._ensure_exists(name)
            chat_path = os.path.join(self.chats_dir(name), chat_file)
            if not os.path.isfile(chat_path):
                raise SessionError(f"聊天文件 '{chat_file}' 不存在")
            config = self._load_config(name)
            config["active_chat"] = chat_file
            self._save_config(name, config)

    def get_messages(self, name: str, chat_file: str) -> list[dict]:
        self._ensure_exists(name)
        chat_path = os.path.join(self.chats_dir(name), chat_file)
        if not os.path.isfile(chat_path):
            raise SessionError(f"聊天文件 '{chat_file}' 不存在")

        with self._chat_file_lock(name, chat_file):
            store = SimpleChatStore.from_persist_path(chat_path)
            keys = store.get_keys()
            if not keys:
                return []

            messages = store.get_messages(keys[0])
            return [
                {
                    "role": m.role.value if hasattr(m.role, "value") else str(m.role),
                    "content": m.content,
                    "additional_kwargs": m.additional_kwargs,
                }
                for m in messages
            ]

    def chat_stream(self, name: str, query: str, chat_file: str = None):
        """
        Stream chat generator.

        Yields SSE event dicts:
            {"type": "start",   "chat_file": "..."}
            {"type": "token",   "token": "..."}
            {"type": "sources", "sources": [...]}
            {"type": "done",    "chat_file": "..."}
            {"type": "error",   "message": "..."}
        """
        started_at = time.monotonic()
        chat_file = self._ensure_chat_target(name, query, chat_file)
        with self._chat_file_lock(name, chat_file):
            chat_path = None
            store = None
            try:
                config, chat_file, chat_path, store = self._prepare_chat_turn(name, query, chat_file)

                yield {"type": "start", "chat_file": chat_file}

                kb_name = config.get("kb_name")
                if not kb_name:
                    raise SessionError(f"会话 '{name}' 未绑定知识库")
                if not _kb.exists(kb_name):
                    raise SessionError(f"知识库 '{kb_name}' 不存在")

                db = chromadb.PersistentClient(path=_kb.vector_db_path(kb_name))
                try:
                    chroma_collection = db.get_collection("kb_index")
                except Exception:
                    raise SessionError(f"知识库 '{kb_name}' 中未找到索引数据，请先在知识库中索引文件")

                if chroma_collection.count() == 0:
                    raise SessionError(f"知识库 '{kb_name}' 中没有向量数据，请先在知识库中索引文件")

                _ensure_models_initialized()

                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
                index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
                top_k = config.get("top_k", self.DEFAULT_TOP_K)
                top_n = config.get("top_n", self.DEFAULT_TOP_N)
                retriever_mode = config.get("retriever_mode", self.DEFAULT_RETRIEVER_MODE)

                logger.debug(
                    "query | stream start session=%s kb=%s top_k=%d top_n=%d mode=%s chat=%s query=%s",
                    name,
                    kb_name,
                    top_k,
                    top_n,
                    retriever_mode,
                    chat_file,
                    query,
                )

                # 重新排序
                reranker = _get_reranker(top_n=top_n)
                # 过滤低相似度结果
                score_filter = SimilarityPostprocessor(similarity_cutoff=0.1)
                retriever = build_retriever(index, kb_name, top_k=top_k, mode=retriever_mode)
                system_prompt = self._normalize_system_prompt(config.get("system_prompt", ""))
                query_engine = RetrieverQueryEngine.from_args(
                    retriever=retriever,
                    node_postprocessors=[reranker, score_filter],
                    text_qa_template=PromptTemplate(system_prompt) if system_prompt else None,
                    streaming=True,
                )
                response = query_engine.query(query)

                answer_buf = []
                for chunk in response.response_gen:
                    if chunk:
                        answer_buf.append(chunk)
                        yield {"type": "token", "token": chunk}

                answer = "".join(answer_buf)
                sources = self._extract_sources(response)
                hint = self._build_retrieval_hint(sources, top_k=top_k, top_n=top_n)
                if hint:
                    answer += hint
                    yield {"type": "token", "token": hint}

                store.add_message(
                    name,
                    ChatMessage(
                        role=MessageRole.ASSISTANT,
                        content=answer,
                        additional_kwargs={"sources": sources} if sources else {},
                    ),
                )
                store.persist(chat_path)

                elapsed = time.monotonic() - started_at
                ans_preview = answer[:100].replace("\n", " ")
                source_scores = [s["score"] for s in sources if s["score"] is not None]
                score_summary = ""
                if source_scores:
                    score_summary = f" score_min={min(source_scores):.4f} score_max={max(source_scores):.4f}"
                logger.debug(
                    "query | stream done session=%s sources=%d elapsed=%.2fs ans_len=%d%s chat=%s ans_pfx=%s",
                    name,
                    len(sources),
                    elapsed,
                    len(answer),
                    score_summary,
                    chat_file,
                    ans_preview,
                )

                yield {"type": "sources", "sources": sources}
                yield {"type": "done", "chat_file": chat_file}
            except Exception as exc:
                elapsed = time.monotonic() - started_at
                error = self._build_stream_error(exc)
                log_fn = logger.debug if isinstance(exc, SessionError) else logger.error
                log_fn("query | stream error session=%s elapsed=%.2fs err=%s", name, elapsed, error["message"])
                if store is not None and chat_path is not None:
                    self._append_assistant_error(store, name, chat_path, error["message"])
                yield {"type": "error", **error}

    def chat(self, name: str, query: str, chat_file: str = None) -> dict:
        started_at = time.monotonic()
        chat_file = self._ensure_chat_target(name, query, chat_file)
        with self._chat_file_lock(name, chat_file):
            chat_path = None
            store = None
            try:
                config, chat_file, chat_path, store = self._prepare_chat_turn(name, query, chat_file)

                kb_name = config.get("kb_name")
                if not kb_name:
                    raise SessionError(f"会话 '{name}' 未绑定知识库")
                if not _kb.exists(kb_name):
                    raise SessionError(f"知识库 '{kb_name}' 不存在")

                _ensure_models_initialized()

                db = chromadb.PersistentClient(path=_kb.vector_db_path(kb_name))
                try:
                    chroma_collection = db.get_collection("kb_index")
                except Exception:
                    raise SessionError(f"知识库 '{kb_name}' 中未找到索引数据")

                if chroma_collection.count() == 0:
                    raise SessionError(f"知识库 '{kb_name}' 中没有向量数据")

                vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
                index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
                top_k = config.get("top_k", self.DEFAULT_TOP_K)
                top_n = config.get("top_n", self.DEFAULT_TOP_N)
                retriever_mode = config.get("retriever_mode", self.DEFAULT_RETRIEVER_MODE)

                logger.debug(
                    "query | sync start session=%s kb=%s top_k=%d top_n=%d mode=%s chat=%s query=%s",
                    name,
                    kb_name,
                    top_k,
                    top_n,
                    retriever_mode,
                    chat_file,
                    query,
                )

                retriever = build_retriever(index, kb_name, top_k=top_k, mode=retriever_mode)
                # 重新排序
                reranker = _get_reranker(top_n=top_n)
                # 过滤低相似度结果
                score_filter = SimilarityPostprocessor(similarity_cutoff=0.1)
                system_prompt = self._normalize_system_prompt(config.get("system_prompt", ""))
                query_engine = RetrieverQueryEngine.from_args(
                    retriever=retriever,
                    node_postprocessors=[reranker, score_filter],
                    text_qa_template=PromptTemplate(system_prompt) if system_prompt else None,
                )
                response = query_engine.query(query)

                answer = str(response)
                sources = self._extract_sources(response)
                hint = self._build_retrieval_hint(sources, top_k=top_k, top_n=top_n)
                if hint:
                    answer += hint

                answer_with_sources = answer
                if sources:
                    answer_with_sources += "\n\n---\n来源:\n"
                    for index_number, source in enumerate(sources, start=1):
                        answer_with_sources += f"\n[{index_number}] (相关度 {source['score']}) {source['text']}"

                store.add_message(name, ChatMessage(role=MessageRole.ASSISTANT, content=answer_with_sources))
                store.persist(chat_path)

                elapsed = time.monotonic() - started_at
                ans_preview = answer[:100].replace("\n", " ")
                source_scores = [s["score"] for s in sources if s["score"] is not None]
                score_summary = ""
                if source_scores:
                    score_summary = f" score_min={min(source_scores):.4f} score_max={max(source_scores):.4f}"
                logger.debug(
                    "query | sync done session=%s sources=%d elapsed=%.2fs ans_len=%d%s chat=%s ans_pfx=%s",
                    name,
                    len(sources),
                    elapsed,
                    len(answer),
                    score_summary,
                    chat_file,
                    ans_preview,
                )

                return {
                    "query": query,
                    "answer": answer,
                    "sources": sources,
                    "chat_file": chat_file,
                    "chat_path": chat_path,
                }
            except Exception as exc:
                error = self._build_stream_error(exc)
                if store is not None and chat_path is not None:
                    self._append_assistant_error(store, name, chat_path, error["message"])
                raise

    def get_config(self, name: str) -> dict:
        with self._session_config_lock(name):
            self._ensure_exists(name)
            cfg = dict(self._load_config(name))
        return cfg

    def update_config(self, name: str, **kwargs) -> dict:
        with self._session_config_lock(name):
            self._ensure_exists(name)
            cfg = self._load_config(name)

            for key, value in kwargs.items():
                if key in ("top_k", "top_n"):
                    if not isinstance(value, int) or value < 1:
                        raise SessionError(f"{key} MUST be >= 1, got {value}")
                    cfg[key] = value
                elif key == "retriever_mode":
                    if value not in ("hybrid", "vector-only"):
                        raise SessionError(f"retriever_mode MUST be 'hybrid' or 'vector-only', got '{value}'")
                    cfg[key] = value
                elif key == "system_prompt":
                    if not isinstance(value, str):
                        raise SessionError("system_prompt MUST be a string")
                    cfg[key] = value
                else:
                    raise SessionError(f"不支持的配置项: {key}")

            self._save_config(name, cfg)
            return cfg

    def _append_assistant_error(self, store: SimpleChatStore, name: str, chat_path: str, message: str):
        store.add_message(name, ChatMessage(role=MessageRole.ASSISTANT, content=f"❌ {message}"))
        store.persist(chat_path)

    def _resolve_chat_target(self, name: str, chat_file: str = None) -> tuple[dict, str, str]:
        self._ensure_exists(name)
        config = self._load_config(name)
        if chat_file:
            chat_path = os.path.join(self.chats_dir(name), chat_file)
            if not os.path.isfile(chat_path):
                raise SessionError(f"聊天文件 '{chat_file}' 不存在")
            return config, chat_file, chat_path

        chat_file = self._ensure_chat_target(name, "", None)
        config = self._load_config(name)
        chat_path = os.path.join(self.chats_dir(name), chat_file)
        return config, chat_file, chat_path

    def _prepare_chat_turn(self, name: str, query: str, chat_file: str = None) -> tuple[dict, str, str, SimpleChatStore]:
        config, chat_file, chat_path = self._resolve_chat_target(name, chat_file)
        store = SimpleChatStore.from_persist_path(chat_path)
        store.add_message(name, ChatMessage(role=MessageRole.USER, content=query))
        store.persist(chat_path)
        return config, chat_file, chat_path, store

    def _ensure_chat_target(self, name: str, query: str, chat_file: str = None) -> str:
        with self._session_config_lock(name):
            self._ensure_exists(name)
            config = self._load_config(name)
            if chat_file:
                chat_path = os.path.join(self.chats_dir(name), chat_file)
                if not os.path.isfile(chat_path):
                    raise SessionError(f"聊天文件 '{chat_file}' 不存在")
            else:
                chat_file = self._create_chat_file_locked(name, config)

            self._ensure_chat_preview_locked(name, config, chat_file, query)
            return chat_file

    def _create_chat_file_locked(self, name: str, config: dict) -> str:
        filename = self._gen_chat_filename(name)
        store = SimpleChatStore()
        store.persist(os.path.join(self.chats_dir(name), filename))
        config["active_chat"] = filename
        self._save_config(name, config)
        return filename

    def _ensure_chat_preview_locked(self, name: str, config: dict, chat_file: str, query: str):
        if not query:
            return
        previews = dict(config.get("chat_previews", {}))
        if chat_file in previews:
            return
        preview = query[:15].replace("\n", " ")
        previews[chat_file] = preview + ("..." if len(query) > 15 else "")
        config["chat_previews"] = previews
        self._save_config(name, config)

    def _normalize_system_prompt(self, system_prompt: str) -> str:
        if not system_prompt:
            return ""
        if "{context_str}" in system_prompt:
            return system_prompt
        return system_prompt + self.CONTEXT_SUFFIX

    def _build_retrieval_hint(self, sources: list[dict], top_k: int, top_n: int) -> str:
        if not sources:
            return ""

        cap = min(top_k, top_n)
        if cap < 4 or len(sources) != cap:
            return ""

        scores = [source.get("score") for source in sources]
        if any(score is None for score in scores):
            return ""

        high_score_count = sum(1 for score in scores if score >= 0.45)
        if high_score_count / cap < 0.6:
            return ""
        if min(scores) < 0.30:
            return ""

        return "\n\n**💡 " + self.RETRIEVAL_HINT_TEXT.format(cap=cap) + "**"

    def _extract_sources(self, response) -> list[dict]:
        sources = []
        if hasattr(response, "source_nodes") and response.source_nodes:
            for node in response.source_nodes:
                score = node.score if hasattr(node, "score") else None
                sources.append(
                    {
                        "text": node.text.strip(),
                        "score": round(float(score), 4) if score is not None else None,
                    }
                )
        return sources

    def _build_stream_error(self, exc: Exception) -> dict:
        message = str(exc)
        if isinstance(exc, SessionError):
            if "未绑定知识库" in message:
                return {"code": "KB_NOT_BOUND", "category": "kb", "message": message}
            if "知识库" in message and "不存在" in message:
                return {"code": "KB_NOT_FOUND", "category": "kb", "message": message}
            if "未找到索引数据" in message:
                return {"code": "KB_INDEX_MISSING", "category": "kb", "message": message}
            if "没有向量数据" in message:
                return {"code": "KB_VECTOR_EMPTY", "category": "kb", "message": message}
            return {"code": "RUNTIME_ERROR", "category": "runtime", "message": message}
        if isinstance(exc, (ConnectionError, TimeoutError, ValueError)):
            return {"code": "MODEL_UNAVAILABLE", "category": "model", "message": message}
        return {"code": "RUNTIME_ERROR", "category": "runtime", "message": f"内部错误: {exc}"}

    def _load_config(self, name: str) -> dict:
        path = self.config_path(name)
        if not os.path.isfile(path):
            return {
                "kb_name": None,
                "active_chat": None,
                "top_k": self.DEFAULT_TOP_K,
                "top_n": self.DEFAULT_TOP_N,
                "retriever_mode": self.DEFAULT_RETRIEVER_MODE,
                "system_prompt": self.DEFAULT_SYSTEM_PROMPT,
                "chat_previews": {},
            }

        with open(path, "r", encoding="utf-8") as handle:
            cfg = json.load(handle)

        if "top_k" not in cfg:
            cfg["top_k"] = self.DEFAULT_TOP_K
        if "top_n" not in cfg:
            cfg["top_n"] = self.DEFAULT_TOP_N
        if "retriever_mode" not in cfg:
            cfg["retriever_mode"] = self.DEFAULT_RETRIEVER_MODE
        if not cfg.get("system_prompt"):
            cfg["system_prompt"] = self.DEFAULT_SYSTEM_PROMPT
        if "chat_previews" not in cfg:
            cfg["chat_previews"] = {}
        return cfg

    def _save_config(self, name: str, data: dict):
        self._save_config_file(self.config_path(name), data)

    def _save_config_file(self, config_path: str, data: dict):
        config_dir = os.path.dirname(config_path)
        os.makedirs(config_dir, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(prefix="config.", suffix=".tmp", dir=config_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, config_path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def _gen_chat_filename(self, name: str) -> str:
        base = datetime.now().strftime("%Y_%m_%d_%H_%M")
        cdir = self.chats_dir(name)
        os.makedirs(cdir, exist_ok=True)

        filename = f"{base}.json"
        if not os.path.isfile(os.path.join(cdir, filename)):
            return filename

        index = 1
        while True:
            filename = f"{base}_{index}.json"
            if not os.path.isfile(os.path.join(cdir, filename)):
                return filename
            index += 1

    def _count_chat_messages(self, fpath: str) -> int:
        try:
            store = SimpleChatStore.from_persist_path(fpath)
            keys = store.get_keys()
            return sum(len(store.get_messages(key)) for key in keys)
        except Exception:
            return 0

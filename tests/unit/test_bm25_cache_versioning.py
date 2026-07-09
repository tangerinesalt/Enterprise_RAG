from pathlib import Path

from app.modules.kb_manager import KnowledgeBase
from app.modules.retrieval import retriever as retriever_module


class _FakeCollection:
    def __init__(self, ids, documents):
        self._ids = ids
        self._documents = documents

    def count(self) -> int:
        return len(self._ids)

    def get(self, include=None):
        return {"ids": list(self._ids), "documents": list(self._documents)}


def test_bm25_cache_rebuilds_when_corpus_version_changes_with_same_chunk_count(tmp_path: Path, monkeypatch):
    kb = KnowledgeBase(str(tmp_path / "kb-root"))
    kb.create("demo")
    retriever_module._bm25_index_cache.clear()

    collection = _FakeCollection(["1", "2"], ["old alpha", "old beta"])
    build_snapshots = []

    class _FakeBM25Retriever:
        def __init__(self, documents):
            self.documents = documents

    def fake_from_defaults(nodes, tokenizer, similarity_top_k):
        docs = [node.text for node in nodes]
        build_snapshots.append(docs)
        return _FakeBM25Retriever(docs)

    monkeypatch.setattr(retriever_module, "_kb", kb)
    monkeypatch.setattr(retriever_module.BM25Retriever, "from_defaults", fake_from_defaults)

    first = retriever_module._build_bm25_retriever("demo", top_k=5, collection=collection)
    assert first.documents == ["old alpha", "old beta"]

    collection._documents = ["new alpha", "new beta"]
    kb.bump_corpus_version("demo")

    second = retriever_module._build_bm25_retriever("demo", top_k=5, collection=collection)
    assert second.documents == ["new alpha", "new beta"]
    assert second is not first
    assert build_snapshots == [["old alpha", "old beta"], ["new alpha", "new beta"]]


def test_bm25_cache_separates_top_k_values(tmp_path: Path, monkeypatch):
    """不同 top_k 值应各自独立缓存，互不污染。"""
    kb = KnowledgeBase(str(tmp_path / "kb-root"))
    kb.create("demo")
    retriever_module._bm25_index_cache.clear()

    collection = _FakeCollection(["1", "2", "3"], ["alpha", "beta", "gamma"])
    build_snapshots = []

    class _FakeBM25Retriever:
        def __init__(self, documents):
            self.documents = documents

    def fake_from_defaults(nodes, tokenizer, similarity_top_k):
        docs = [node.text for node in nodes]
        build_snapshots.append((similarity_top_k, docs))
        return _FakeBM25Retriever(docs)

    monkeypatch.setattr(retriever_module, "_kb", kb)
    monkeypatch.setattr(retriever_module.BM25Retriever, "from_defaults", fake_from_defaults)

    # 第一次用 top_k=2
    r1 = retriever_module._build_bm25_retriever("demo", top_k=2, collection=collection)
    # 第二次用 top_k=5
    r2 = retriever_module._build_bm25_retriever("demo", top_k=5, collection=collection)
    # 第三次用 top_k=2 → 应命中缓存的 r1，不重建
    r3 = retriever_module._build_bm25_retriever("demo", top_k=2, collection=collection)
    # 第四次用 top_k=5 → 应命中缓存的 r2，不重建
    r4 = retriever_module._build_bm25_retriever("demo", top_k=5, collection=collection)

    assert r1 is r3, "top_k=2 应是相同缓存对象"
    assert r2 is r4, "top_k=5 应是相同缓存对象"
    assert r1 is not r2, "不同 top_k 不应共享缓存"
    # 只应构建了 2 次（top_k=2 和 top_k=5 各一次）
    assert build_snapshots == [(2, ["alpha", "beta", "gamma"]), (5, ["alpha", "beta", "gamma"])]

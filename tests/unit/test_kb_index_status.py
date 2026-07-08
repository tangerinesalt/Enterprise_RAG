"""Tests: KB indexing status consistency.

Verifies that both sync and streaming indexing paths persist file-level
chunk counts via set_file_status() instead of collection-wide totals.
"""

import json
from pathlib import Path

from app.modules.kb_manager.knowledge_base import KnowledgeBase
from app.modules.kb_manager.indexer import Indexer


class _FakeChromaCollection:
    """A chroma collection stub that returns a deliberately wrong .count()
    to prove the fix does not rely on collection-level totals."""

    def count(self) -> int:
        return 99999  # deliberately wrong — tests must verify this is NOT used

    def get(self, where=None):
        return {"ids": []}

    def delete(self, ids):
        pass


class _FakeChromaDB:
    def get_or_create_collection(self, name, metadata=None):
        return _FakeChromaCollection()

    def get_collection(self, name):
        return _FakeChromaCollection()


def _setup_test_kb(tmp_path: Path) -> tuple[KnowledgeBase, str]:
    """Create a test KB with one .txt file and return (kb, filename)."""
    kb = KnowledgeBase(str(tmp_path / "kb_root"))
    kb.create("test-kb")

    filename = "hello.txt"
    file_path = kb.file_path("test-kb", filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("Hello world. " * 50)

    kb.set_file_status("test-kb", filename, "pending")
    return kb, filename


def test_index_file_writes_status_with_file_level_chunks(tmp_path, monkeypatch):
    """Sync index_file should write indexed + file-level chunk count to status file."""
    kb, filename = _setup_test_kb(tmp_path)

    # Point the global _kb to our test KB so ensure_exists/etc. resolve correctly
    monkeypatch.setattr("app.modules.kb_manager.indexer._kb", kb)

    # Mock chroma/vector-store layer — keep chunking real
    monkeypatch.setattr("app.modules.kb_manager.indexer.chromadb.PersistentClient",
                        lambda path: _FakeChromaDB())
    monkeypatch.setattr("app.modules.kb_manager.indexer.ChromaVectorStore",
                        lambda chroma_collection: None)
    monkeypatch.setattr("app.modules.kb_manager.indexer.VectorStoreIndex",
                        type("FakeVSI", (), {"__init__": lambda self, nodes=None, storage_context=None: None}))

    idx = Indexer()
    chunk_count = idx.index_file("test-kb", filename)

    # Result should come from len(nodes), not collection.count()
    assert chunk_count > 0, "Should have chunked the document"
    assert chunk_count != 99999, "Should NOT use collection.count()"

    # Status file should reflect the indexed state
    status = kb.get_file_status("test-kb", filename)
    assert status["status"] == "indexed"
    assert status["chunks"] == chunk_count


def test_index_file_stream_writes_file_level_chunks(tmp_path, monkeypatch):
    """Stream index_file_stream should emit index_done with len(nodes) and persist same."""
    kb, filename = _setup_test_kb(tmp_path)

    monkeypatch.setattr("app.modules.kb_manager.indexer._kb", kb)
    monkeypatch.setattr("app.modules.kb_manager.indexer.chromadb.PersistentClient",
                        lambda path: _FakeChromaDB())
    monkeypatch.setattr("app.modules.kb_manager.indexer.ChromaVectorStore",
                        lambda chroma_collection: None)
    monkeypatch.setattr("app.modules.kb_manager.indexer.VectorStoreIndex",
                        type("FakeVSI", (), {"__init__": lambda self, nodes=None, storage_context=None: None}))

    # Avoid real embedding calls — use MockEmbedding (a BaseEmbedding subclass)
    from llama_index.core.embeddings import MockEmbedding

    monkeypatch.setattr("app.modules.kb_manager.indexer.Settings.embed_model", MockEmbedding(embed_dim=768))

    idx = Indexer()
    events = list(idx.index_file_stream("test-kb", filename))

    # Find the index_done event
    done_events = [e for e in events if e["type"] == "index_done"]
    assert len(done_events) == 1

    payload = done_events[0]
    assert payload["chunks"] > 0
    assert payload["chunks"] != 99999  # not collection.count()

    # Status file should match
    status = kb.get_file_status("test-kb", filename)
    assert status["status"] == "indexed"
    assert status["chunks"] == payload["chunks"]


def test_index_file_status_persists_across_reload(tmp_path, monkeypatch):
    """Status written by index_file survives status file reload (JSON round-trip)."""
    kb, filename = _setup_test_kb(tmp_path)

    monkeypatch.setattr("app.modules.kb_manager.indexer._kb", kb)
    monkeypatch.setattr("app.modules.kb_manager.indexer.chromadb.PersistentClient",
                        lambda path: _FakeChromaDB())
    monkeypatch.setattr("app.modules.kb_manager.indexer.ChromaVectorStore",
                        lambda chroma_collection: None)
    monkeypatch.setattr("app.modules.kb_manager.indexer.VectorStoreIndex",
                        type("FakeVSI", (), {"__init__": lambda self, nodes=None, storage_context=None: None}))

    idx = Indexer()
    chunk_count = idx.index_file("test-kb", filename)

    # Reload the KB and verify status is preserved
    kb2 = KnowledgeBase(str(tmp_path / "kb_root"))
    status = kb2.get_file_status("test-kb", filename)
    assert status["status"] == "indexed"
    assert status["chunks"] == chunk_count

    # Raw JSON file should have the correct structure
    status_path = Path(kb2._index_status_path("test-kb"))
    assert status_path.exists()
    raw = json.loads(status_path.read_text(encoding="utf-8"))
    assert raw["files"][filename]["status"] == "indexed"
    assert raw["files"][filename]["chunks"] == chunk_count

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers import kb as kb_router
from app.modules.kb_manager import KnowledgeBase


def _make_client(tmp_path, monkeypatch):
    test_kb = KnowledgeBase(str(tmp_path / "kb-root"))
    test_kb.create("demo")
    monkeypatch.setattr(kb_router, "_kb", test_kb)

    app = FastAPI()
    app.include_router(kb_router.router, prefix="/api/kb")
    return TestClient(app), test_kb


def test_upload_strips_directory_segments_before_saving(tmp_path, monkeypatch):
    client, test_kb = _make_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/kb/upload",
        data={"name": "demo"},
        files=[("files", ("nested/path/report.txt", b"hello", "text/plain"))],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["saved"] == ["report.txt"]
    assert test_kb.file_exists("demo", "report.txt")


def test_upload_rejects_invalid_leaf_filename_after_stripping(tmp_path, monkeypatch):
    client, _test_kb = _make_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/kb/upload",
        data={"name": "demo"},
        files=[("files", ("nested/path/CON.txt", b"hello", "text/plain"))],
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False


def test_upload_and_index_indexes_stripped_leaf_filename(tmp_path, monkeypatch):
    client, _test_kb = _make_client(tmp_path, monkeypatch)
    seen = []

    class _FakeIndexer:
        def index_file(self, name: str, filename: str):
            seen.append((name, filename))
            return 1

    monkeypatch.setattr(kb_router, "_indexer", _FakeIndexer())

    response = client.post(
        "/api/kb/upload-and-index",
        data={"name": "demo"},
        files=[("files", ("nested/path/report.txt", b"hello", "text/plain"))],
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["data"]["saved"] == ["report.txt"]
    assert seen == [("demo", "report.txt")]


@pytest.mark.parametrize(
    "bad_filename",
    ["bad?.txt", "bad*.txt", "bad<.txt", "bad>.txt", "bad|.txt", "bad:.txt"],
)
def test_upload_rejects_windows_illegal_chars(tmp_path, monkeypatch, bad_filename: str):
    client, _test_kb = _make_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/kb/upload",
        data={"name": "demo"},
        files=[("files", (bad_filename, b"hello", "text/plain"))],
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False


@pytest.mark.parametrize(
    "bad_filename",
    ["bad?.txt", "bad*.txt", "bad<.txt", "bad>.txt", "bad|.txt", "bad:.txt"],
)
def test_upload_and_index_rejects_windows_illegal_chars(tmp_path, monkeypatch, bad_filename: str):
    client, _test_kb = _make_client(tmp_path, monkeypatch)

    response = client.post(
        "/api/kb/upload-and-index",
        data={"name": "demo"},
        files=[("files", (bad_filename, b"hello", "text/plain"))],
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["ok"] is False

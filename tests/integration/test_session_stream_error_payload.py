import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers import session as session_router


def test_chat_stream_error_event_includes_code_category_and_message(monkeypatch):
    class FakeSession:
        def chat_stream(self, name: str, query: str, chat_file: str = None):
            yield {
                "type": "error",
                "code": "KB_INDEX_MISSING",
                "category": "kb",
                "message": "missing index",
            }

    monkeypatch.setattr(session_router, "_session", FakeSession())

    app = FastAPI()
    app.include_router(session_router.router, prefix="/api/session")

    with TestClient(app) as client:
        response = client.post("/api/session/chat/stream", json={"name": "demo", "query": "hello"})

    assert response.status_code == 200
    assert "event: error" in response.text

    data_line = next(line for line in response.text.splitlines() if line.startswith("data: "))
    payload = json.loads(data_line[len("data: "):])

    assert payload == {
        "code": "KB_INDEX_MISSING",
        "category": "kb",
        "message": "missing index",
    }

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers import session as session_router
from app.modules.session import session_manager as sm
from app.modules.session.session_manager import SessionManager


def _build_app():
    app = FastAPI()
    app.include_router(session_router.router, prefix="/api/session")
    return app


def test_session_api_omits_removed_active_chat_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(sm, "SESSION_ROOT", str(tmp_path / "sessions"))
    manager = SessionManager()
    manager.create("demo")
    manager.new_chat("demo")
    monkeypatch.setattr(session_router, "_session", manager)

    with TestClient(_build_app()) as client:
        session_response = client.get("/api/session/demo")
        list_response = client.get("/api/session")
        chats_response = client.get("/api/session/demo/chats")

    assert session_response.status_code == 200
    assert list_response.status_code == 200
    assert chats_response.status_code == 200

    session_payload = session_response.json()["data"]
    list_payload = list_response.json()["data"]
    chats_payload = chats_response.json()["data"]["chats"]

    assert "active_chat" not in session_payload
    assert all("active_chat" not in item for item in list_payload)
    assert all("is_active" not in item for item in chats_payload)


def test_session_select_endpoint_is_removed():
    with TestClient(_build_app()) as client:
        response = client.post("/api/session/select", json={"name": "demo", "chat_file": "c.json"})

    assert response.status_code in {404, 405}

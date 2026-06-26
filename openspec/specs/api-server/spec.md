## ADDED Requirements

### Requirement: Server SHALL start on configurable port

The FastAPI server SHALL start on port 8000 by default with CORS enabled.

#### Scenario: Server starts
- **WHEN** running `uvicorn app.api.server:app --reload --port 8000`
- **THEN** the server is available at `http://localhost:8000`
- **THEN** CORS headers allow all origins

### Requirement: Server SHALL have health check endpoint

The server SHALL provide a health check.

#### Scenario: GET /api/health
- **WHEN** client sends `GET /api/health`
- **THEN** response returns `{"ok": true, "status": "running"}`

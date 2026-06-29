## ADDED Requirements

### Requirement: API SHALL update session retrieval config

The system SHALL provide an endpoint to partially update session config (top_k, top_n).

#### Scenario: PATCH /api/session/{name}/config
- **WHEN** client sends `PATCH /api/session/my-session/config` with `{"top_k": 10}`
- **THEN** response is `{"ok": true, "data": {"top_k": 10, "top_n": 5}}`
- **THEN** config.json is persisted with the updated value

#### Scenario: PATCH rejects invalid values
- **WHEN** client sends `PATCH /api/session/my-session/config` with `{"top_k": -1}`
- **THEN** response is `{"ok": false, "error": "top_k MUST be >= 1"}`
- **THEN** config.json is NOT modified

## MODIFIED Requirements

### Requirement: API SHALL return session retrieval params in detail

#### Scenario: GET /api/session/{name} includes params
- **WHEN** client sends `GET /api/session/my-session`
- **THEN** response includes `"top_k"` and `"top_n"` alongside existing fields

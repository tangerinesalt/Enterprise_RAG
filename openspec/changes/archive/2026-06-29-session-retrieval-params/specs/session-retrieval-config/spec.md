## ADDED Requirements

### Requirement: Session SHALL persist retrieval parameters in config

The session config.json SHALL store `top_k` and `top_n` fields controlling retrieval behavior.

#### Scenario: Default values on create
- **WHEN** a new session is created via CLI `session create my-session` or API `POST /api/session`
- **THEN** `sessions/my-session/config.json` contains `"top_k": 8` and `"top_n": 5`
- **THEN** these values are written at creation time

#### Scenario: Missing fields fall back to defaults
- **WHEN** an existing session config.json lacks `top_k` or `top_n` fields
- **THEN** the system uses `top_k=8` and `top_n=5` as implicit defaults
- **THEN** the config file is NOT modified by a read-only operation

### Requirement: User SHALL view retrieval parameters

The system SHALL display the current `top_k` and `top_n` values for a session.

#### Scenario: CLI show config
- **WHEN** user runs `session config my-session`
- **THEN** output shows `top_k: 8` and `top_n: 5` (or current values)

#### Scenario: API show config
- **WHEN** client sends `GET /api/session/my-session`
- **THEN** response includes `"top_k": 8` and `"top_n": 5` in the session info

### Requirement: User SHALL modify retrieval parameters

The system SHALL allow updating `top_k` and `top_n` per session.

#### Scenario: CLI modify single param
- **WHEN** user runs `session config my-session --set top_k=10`
- **THEN** config.json is updated with `"top_k": 10`
- **THEN** `top_n` remains unchanged

#### Scenario: CLI modify both params
- **WHEN** user runs `session config my-session --set top_k=10 --set top_n=7`
- **THEN** config.json is updated with `"top_k": 10, "top_n": 7`

#### Scenario: API modify config
- **WHEN** client sends `PATCH /api/session/my-session/config` with `{"top_k": 12}`
- **THEN** config.json is updated with `"top_k": 12`
- **THEN** only the specified fields are changed

#### Scenario: Reject invalid values
- **WHEN** user attempts to set `top_k=0` or `top_n=-1` via CLI or API
- **THEN** the system rejects with an error message: `top_k MUST be >= 1`
- **THEN** config.json is NOT modified

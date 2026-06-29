## MODIFIED Requirements

### Requirement: User SHALL create a session by name

The system SHALL create a new session directory with config file containing default top_k and top_n values.

#### Scenario: Create a new session
- **WHEN** user runs `python -m app.modules.kb_manager.cli session create my-session`
- **THEN** directory `sessions/my-session/` is created
- **THEN** subdirectory `sessions/my-session/chats/` is created
- **THEN** `sessions/my-session/config.json` is created with `{"kb_name": null, "active_chat": null, "top_k": 8, "top_n": 5}`
- **THEN** system prints "Session 'my-session' created"

#### Scenario: Create duplicate session
- **WHEN** user runs `session create my-session` and it already exists
- **THEN** system prints "Session 'my-session' already exists"

### Requirement: User SHALL get session info with retrieval params

The system SHALL return session info including retrieval parameters.

#### Scenario: Info includes top_k and top_n (no change needed)
- **WHEN** user runs `session info my-session` or `GET /api/session/my-session`
- **THEN** the response includes `"top_k"` and `"top_n"` values

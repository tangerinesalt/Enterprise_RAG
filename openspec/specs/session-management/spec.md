## ADDED Requirements

### Requirement: User SHALL create a session by name

The system SHALL create a new session directory with config file.

#### Scenario: Create a new session
- **WHEN** user runs `python -m app.modules.kb_manager.cli session create my-session`
- **THEN** directory `sessions/my-session/` is created
- **THEN** subdirectory `sessions/my-session/chats/` is created
- **THEN** `sessions/my-session/config.json` is created with empty config
- **THEN** system prints "Session 'my-session' created"

#### Scenario: Create duplicate session
- **WHEN** user runs `session create my-session` and it already exists
- **THEN** system prints "Session 'my-session' already exists"

### Requirement: User SHALL bind a knowledge base to a session

The system SHALL save the knowledge base name into the session's config file.

#### Scenario: Bind an existing KB
- **WHEN** user runs `python -m app.modules.kb_manager.cli session bind my-session my-docs`
- **THEN** `sessions/my-session/config.json` is updated with `kb_name: "my-docs"`
- **THEN** system prints "Session 'my-session' bound to knowledge base 'my-docs'"

#### Scenario: Bind to non-existent KB
- **WHEN** user runs `session bind my-session unknown-kb` and the KB doesn't exist
- **THEN** system prints "Knowledge base 'unknown-kb' not found"

#### Scenario: Bind non-existent session
- **WHEN** user runs `session bind unknown-session my-docs`
- **THEN** system prints "Session 'unknown-session' not found"

### Requirement: User SHALL list sessions and chats

The system SHALL support listing all sessions or viewing a session's chat history.

#### Scenario: List all sessions
- **WHEN** user runs `python -m app.modules.kb_manager.cli session list`
- **THEN** system lists all session directories with their bound KB

#### Scenario: List chat files in a session
- **WHEN** user runs `python -m app.modules.kb_manager.cli session list my-session`
- **THEN** system lists all chat JSON files in `sessions/my-session/chats/`

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

#### Scenario: Info includes top_k and top_n
- **WHEN** user runs `session info my-session` or `GET /api/session/my-session`
- **THEN** the response includes `"top_k"` and `"top_n"` values

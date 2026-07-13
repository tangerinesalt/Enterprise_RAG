## MODIFIED Requirements

### Requirement: User SHALL create a session by name

The system SHALL create a new session directory with a config file containing only supported persisted session defaults for retrieval and chat preview behavior.

#### Scenario: Create a new session
- **WHEN** user runs `python -m app.modules.kb_manager.cli session create my-session`
- **THEN** directory `sessions/my-session/` is created
- **THEN** subdirectory `sessions/my-session/chats/` is created
- **THEN** `sessions/my-session/config.json` is created with `{"kb_name": null, "top_k": 8, "top_n": 5}` plus other supported fields such as `system_prompt`, `retriever_mode`, and `chat_previews`
- **THEN** `config.json` does NOT contain `active_chat`
- **THEN** system prints "Session 'my-session' created"

#### Scenario: Create duplicate session
- **WHEN** user runs `session create my-session` and it already exists
- **THEN** system prints "Session 'my-session' already exists"

### Requirement: User SHALL list sessions and chats

The system SHALL support listing all sessions or viewing a session's chat history without displaying any backend-selected-chat marker.

#### Scenario: List all sessions
- **WHEN** user runs `python -m app.modules.kb_manager.cli session list`
- **THEN** system lists all session directories with their bound KB
- **THEN** the output does NOT include `active_chat`

#### Scenario: List chat files in a session
- **WHEN** user runs `python -m app.modules.kb_manager.cli session list my-session`
- **THEN** system lists all chat JSON files in `sessions/my-session/chats/`
- **THEN** the output does NOT mark any chat as backend-active

### Requirement: User SHALL get session info with retrieval params

The system SHALL return session info including retrieval parameters and supported persisted metadata, without any selected-chat field.

#### Scenario: Info includes top_k and top_n
- **WHEN** user runs `session info my-session` or `GET /api/session/my-session`
- **THEN** the response includes `"top_k"` and `"top_n"` values
- **THEN** the response does NOT include `active_chat`

## REMOVED Requirements

### Requirement: Session SHALL treat active_chat as recent-selection metadata
**Reason**: The system no longer persists or exposes any backend-selected-chat metadata.
**Migration**: Clients and operators MUST rely on explicit `chat_file` and frontend-local selection state instead of `active_chat`.

## ADDED Requirements

### Requirement: Session config SHALL tolerate legacy `active_chat` during migration

The system SHALL continue to load legacy session config files that still contain `active_chat`, but persisted config output after any supported write SHALL omit that field.

#### Scenario: Legacy config is readable and rewritten cleanly
- **WHEN** `sessions/my-session/config.json` contains a legacy `active_chat` field from an older version
- **THEN** session info, listing, and chat execution continue to work
- **THEN** after any supported config write, the rewritten `config.json` no longer contains `active_chat`

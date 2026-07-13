## MODIFIED Requirements

### Requirement: API SHALL list all sessions

The system SHALL return a list of all sessions. Session list entries SHALL expose only persisted session metadata that remains authoritative after this change and SHALL NOT include `active_chat`.

#### Scenario: GET /api/session
- **WHEN** client sends `GET /api/session`
- **THEN** response includes session names, bound KBs, and other supported persisted session fields
- **THEN** no session entry includes `active_chat`

### Requirement: API SHALL return session retrieval params in detail

Session detail responses SHALL expose retrieval and chat-summary data without any backend-selected-chat field.

#### Scenario: GET /api/session/{name} includes params without active chat
- **WHEN** client sends `GET /api/session/my-session`
- **THEN** response includes `"top_k"` and `"top_n"` alongside supported session detail fields
- **THEN** response does NOT include `"active_chat"`

## ADDED Requirements

### Requirement: API SHALL list chat files without selection metadata

The system SHALL return chat-list entries based on persisted chat data only and SHALL NOT expose backend active-selection markers.

#### Scenario: GET /api/session/{name}/chats omits `is_active`
- **WHEN** client sends `GET /api/session/my-session/chats`
- **THEN** each chat entry includes its supported persisted identifiers such as `file` and optional `preview`
- **THEN** no chat entry includes `is_active`

### Requirement: API SHALL not provide a backend chat-selection endpoint

The system SHALL not provide an API for persisting a session-global selected chat.

#### Scenario: POST /api/session/select is unsupported
- **WHEN** client sends `POST /api/session/select`
- **THEN** the request is rejected as an unsupported route
- **THEN** no session metadata is created or updated to record a selected chat

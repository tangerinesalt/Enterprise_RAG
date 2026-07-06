## Purpose

Define the REST API endpoints for managing sessions, binding knowledge bases, sending chat requests, and updating session configuration.
## Requirements
### Requirement: API SHALL list all sessions

The system SHALL return a list of all sessions.

#### Scenario: GET /api/session
- **WHEN** client sends `GET /api/session`
- **THEN** response includes session names, bound KBs

### Requirement: API SHALL create a session

The system SHALL create a new session.

#### Scenario: POST /api/session
- **WHEN** client sends `POST /api/session` with `{"name": "my-session"}`
- **THEN** a new session is created

### Requirement: API SHALL bind a knowledge base to a session

The system SHALL bind a KB to a session.

#### Scenario: POST /api/session/bind
- **WHEN** client sends `POST /api/session/bind` with `{"name": "my-session", "kb_name": "my-docs"}`
- **THEN** the session is bound to the KB

### Requirement: API SHALL support chat

The system SHALL accept a query and return an AI-generated answer with sources. When `chat_file` is provided, the API SHALL treat it as the authoritative target chat for that request.

#### Scenario: POST /api/session/chat
- **WHEN** client sends `POST /api/session/chat` with `{"name": "my-session", "query": "问题"}`
- **THEN** the system retrieves context from the bound KB
- **THEN** the LLM generates an answer
- **THEN** response includes `answer`, `sources`, and `chat_file`
- **THEN** the chat is persisted to `SimpleChatStore`

#### Scenario: Chat with existing chat file
- **WHEN** client sends `POST /api/session/chat` with `{"name": "my-session", "query": "继续", "chat_file": "2026_07_06_10_00.json"}`
- **THEN** the existing chat history is loaded from that exact chat file
- **THEN** the response is persisted back to that same chat file

#### Scenario: Stream chat with explicit chat file
- **WHEN** client sends `POST /api/session/chat/stream` with `{"name": "my-session", "query": "继续", "chat_file": "2026_07_06_10_00.json"}`
- **THEN** the stream request uses `2026_07_06_10_00.json` as its target chat
- **THEN** it does NOT require session-global `active_chat` to point at the same file

#### Scenario: Different chat files in one session can progress concurrently
- **WHEN** two requests target the same session but different `chat_file` values
- **THEN** the API allows them to progress concurrently
- **THEN** each request returns and persists against its own target chat file

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

### Requirement: API SHALL return session retrieval params in detail

#### Scenario: GET /api/session/{name} includes params
- **WHEN** client sends `GET /api/session/my-session`
- **THEN** response includes `"top_k"` and `"top_n"` alongside existing fields

### Requirement: Stream chat SHALL emit structured error events

The streaming chat API SHALL return structured error payloads so that clients can branch on stable fields instead of parsing message text.

#### Scenario: Structured KB error event
- **WHEN** `POST /api/session/chat/stream` fails because the bound knowledge base has no index data
- **THEN** the SSE stream emits `event: error`
- **THEN** the payload includes `code`, `category`, and `message`
- **THEN** `category` is `kb`

#### Scenario: Structured model error event
- **WHEN** `POST /api/session/chat/stream` fails because model initialization or provider access fails
- **THEN** the SSE stream emits `event: error`
- **THEN** the payload includes `code`, `category`, and `message`
- **THEN** `category` is `model` or `runtime`

#### Scenario: Error message remains user-visible
- **WHEN** the streaming API emits a structured error event
- **THEN** the payload still includes a human-readable `message`
- **THEN** clients can display the message directly without reconstructing it from the error code

#### Scenario: Error code comes from the defined minimal set
- **WHEN** the streaming API emits an `error` event for this change scope
- **THEN** `code` is one of `KB_NOT_BOUND`, `KB_NOT_FOUND`, `KB_INDEX_MISSING`, `KB_VECTOR_EMPTY`, `MODEL_UNAVAILABLE`, or `RUNTIME_ERROR`
- **THEN** clients can treat the code set as a stable contract for branching and tests


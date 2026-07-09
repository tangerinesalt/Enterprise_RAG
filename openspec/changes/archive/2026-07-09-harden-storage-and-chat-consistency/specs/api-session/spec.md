## MODIFIED Requirements

### Requirement: API SHALL create a session

The system SHALL create a new session, and the provided session name SHALL satisfy the system's path-safe identifier rules.

#### Scenario: POST /api/session
- **WHEN** client sends `POST /api/session` with `{"name": "my-session"}`
- **THEN** a new session is created

#### Scenario: POST /api/session rejects unsafe session name
- **WHEN** client sends `POST /api/session` with a session name containing path separators, `..`, or absolute-path semantics
- **THEN** the API rejects the request
- **THEN** no session directory is created outside or inside the session root for that invalid name

### Requirement: API SHALL support chat

The system SHALL accept a query and return an AI-generated answer with sources. When `chat_file` is provided, the API SHALL treat it as the authoritative target chat for that request, and that target SHALL resolve only within the session's chat directory.

#### Scenario: POST /api/session/chat
- **WHEN** client sends `POST /api/session/chat` with `{"name": "my-session", "query": "闂"}`
- **THEN** the system retrieves context from the bound KB
- **THEN** the LLM generates an answer
- **THEN** response includes `answer`, `sources`, and `chat_file`
- **THEN** the chat is persisted to `SimpleChatStore`

#### Scenario: Chat with existing chat file
- **WHEN** client sends `POST /api/session/chat` with `{"name": "my-session", "query": "缁х画", "chat_file": "2026_07_06_10_00.json"}`
- **THEN** the existing chat history is loaded from that exact chat file
- **THEN** the response is persisted back to that same chat file

#### Scenario: Stream chat with explicit chat file
- **WHEN** client sends `POST /api/session/chat/stream` with `{"name": "my-session", "query": "缁х画", "chat_file": "2026_07_06_10_00.json"}`
- **THEN** the stream request uses `2026_07_06_10_00.json` as its target chat
- **THEN** it does NOT require session-global `active_chat` to point at the same file

#### Scenario: Different chat files in one session can progress concurrently
- **WHEN** two requests target the same session but different `chat_file` values
- **THEN** the API allows them to progress concurrently
- **THEN** each request returns and persists against its own target chat file

#### Scenario: Chat rejects unsafe chat file target
- **WHEN** client sends `/api/session/chat` or `/api/session/chat/stream` with a `chat_file` value that resolves outside `sessions/<name>/chats/`
- **THEN** the API rejects the request
- **THEN** no out-of-root file is read or written

## ADDED Requirements

### Requirement: API SHALL read chat messages only from the session chat root

The system SHALL return chat messages only when the requested `chat_file` resolves within the target session's chat directory.

#### Scenario: GET /api/session/{name}/chats/{chat_file} returns in-root chat
- **WHEN** client requests an existing chat file under `sessions/<name>/chats/`
- **THEN** the API returns that chat's messages

#### Scenario: GET /api/session/{name}/chats/{chat_file} rejects unsafe target
- **WHEN** client requests a `chat_file` that resolves outside the session chat root
- **THEN** the API rejects the request
- **THEN** no out-of-root file is read

### Requirement: API SHALL delete chat files only from the session chat root

The system SHALL delete chat files only when the requested `chat_file` resolves within the target session's chat directory.

#### Scenario: DELETE /api/session/{name}/chats/{chat_file} deletes in-root chat
- **WHEN** client requests deletion of an existing chat file under `sessions/<name>/chats/`
- **THEN** the API deletes that chat file
- **THEN** related session metadata is updated consistently

#### Scenario: DELETE /api/session/{name}/chats/{chat_file} rejects unsafe target
- **WHEN** client sends a `chat_file` that resolves outside the session chat root
- **THEN** the API rejects the request
- **THEN** no out-of-root file is deleted

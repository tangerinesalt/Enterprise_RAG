## MODIFIED Requirements

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

## ADDED Requirements

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

The system SHALL accept a query and return an AI-generated answer with sources.

#### Scenario: POST /api/session/chat
- **WHEN** client sends `POST /api/session/chat` with `{"name": "my-session", "query": "问题"}`
- **THEN** the system retrieves context from the bound KB
- **THEN** the LLM generates an answer
- **THEN** response includes `answer`, `sources`, and `chat_file`
- **THEN** the chat is persisted to SimpleChatStore

#### Scenario: Chat with existing chat file
- **WHEN** client sends `POST /api/session/chat` with `{"name": "my-session", "query": "继续", "chat_file": "2026_06_25.json"}`
- **THEN** the existing chat history is loaded as context

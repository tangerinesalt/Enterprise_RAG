## MODIFIED Requirements

### Requirement: API SHALL support chat

The system SHALL accept a query and return an AI-generated answer with sources, while keeping synchronous and streaming chat persistence semantics aligned.

#### Scenario: POST /api/session/chat
- **WHEN** client sends `POST /api/session/chat` with `{"name": "my-session", "query": "闂"}`
- **THEN** the system retrieves context from the bound KB
- **THEN** the LLM generates an answer
- **THEN** response includes `answer`, `sources`, and `chat_file`
- **THEN** the chat is persisted to SimpleChatStore

#### Scenario: Chat with existing chat file
- **WHEN** client sends `POST /api/session/chat` with `{"name": "my-session", "query": "缁х画", "chat_file": "2026_06_25.json"}`
- **THEN** the existing chat history is loaded as context

#### Scenario: POST /api/session/chat preserves failed turn
- **WHEN** client sends `POST /api/session/chat` and the request fails after entering the chat execution flow
- **THEN** the user question is persisted to the target chat file
- **THEN** an assistant error message is persisted to the same chat file
- **THEN** the API error response does NOT require the client to recreate or delete the chat file

## ADDED Requirements

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

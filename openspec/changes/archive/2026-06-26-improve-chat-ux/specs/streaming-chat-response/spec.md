## ADDED Requirements

### Requirement: Server-Sent Events streaming endpoint
The system SHALL provide a `POST /api/session/chat/stream` endpoint that returns an SSE (Server-Sent Events) stream of the chat response. The endpoint SHALL NOT replace the existing synchronous `POST /api/session/chat` endpoint.

#### Scenario: Client receives tokens as they are generated
- **WHEN** a client sends a POST request to `/api/session/chat/stream` with `{"name": "demo", "query": "What is RAG?"}`
- **THEN** the server returns `Content-Type: text/event-stream` and sends a sequence of SSE events: `start`, multiple `token` events, `sources`, and `done`

#### Scenario: SSE event format
- **WHEN** the server streams a chat response
- **THEN** each event SHALL follow the SSE protocol: `event: <type>\ndata: <json>\n\n`
- **THEN** the `start` event SHALL contain `{"chat_file": "2026_06_25_10_30.json"}`
- **THEN** each `token` event SHALL contain `{"token": "<partial text>"}`
- **THEN** the `sources` event SHALL contain `{"sources": [{"text": "...", "score": 0.92}]}`
- **THEN** the `done` event SHALL contain `{"chat_file": "2026_06_25_10_30.json"}`

#### Scenario: Error event
- **WHEN** an error occurs during streaming (e.g., KB not found, no index data, session error)
- **THEN** the server SHALL send an `error` event with `{"message": "..."}` and close the stream
- **THEN** the HTTP response status SHALL be 200 (SSE protocol — error is an event, not a status code)

#### Scenario: Existing sync endpoint unchanged
- **WHEN** a client sends a POST request to the existing `/api/session/chat` endpoint
- **THEN** the server SHALL return the original JSON response exactly as before

### Requirement: Streaming chat core logic
The system SHALL support streaming token generation from the LLM in `SessionManager`. The existing non-streaming `chat()` method SHALL remain functional.

#### Scenario: Stream generator yields tokens and collects full response
- **WHEN** `SessionManager.chat_stream(name, query, chat_file)` is called
- **THEN** it SHALL execute retrieval (ChromaDB vector search) then LLM generation with `streaming=True`
- **THEN** it SHALL yield each token as it is generated
- **THEN** it SHALL collect all yielded tokens into a complete answer string
- **THEN** after all tokens are yielded, it SHALL persist the user message and full assistant answer to `SimpleChatStore`
- **THEN** it SHALL yield the sources list
- **THEN** it SHALL yield the done signal with the chat filename

### Requirement: Frontend stream consumption
The frontend SHALL consume the SSE stream using `fetch` + `ReadableStream` (POST method) and render tokens incrementally.

#### Scenario: Typing effect on receiving tokens
- **WHEN** the frontend receives a `token` SSE event
- **THEN** the token content SHALL be appended to the current assistant message in the chat UI immediately
- **THEN** the message area SHALL auto-scroll to follow the latest content

#### Scenario: Sources displayed after streaming
- **WHEN** the frontend receives a `sources` SSE event
- **THEN** the sources SHALL be displayed below the assistant message in collapsible format

#### Scenario: Error handling
- **WHEN** the frontend receives an `error` SSE event
- **THEN** the error message SHALL be displayed as an assistant message with an error indicator (❌)

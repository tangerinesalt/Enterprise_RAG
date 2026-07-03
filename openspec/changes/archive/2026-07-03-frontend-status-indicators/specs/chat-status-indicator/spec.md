## ADDED Requirements

### Requirement: SSE protocol SHALL emit phase events

The chat SSE stream SHALL emit a `phase` event between `start` and the first `token` to indicate the current processing stage.

#### Scenario: Retrieval phase event

- **WHEN** a chat stream starts
- **AND** the backend begins retrieving relevant chunks from the knowledge base
- **THEN** the stream SHALL emit `event: phase\ndata: {"phase": "retrieving"}\n\n` before the first retrieval query
- **AND** the event SHALL be emitted **after** the `start` event and **before** any `token` event

#### Scenario: Generation phase event

- **WHEN** retrieval and reranking complete
- **AND** the LLM begins generating the response
- **THEN** the stream SHALL emit `event: phase\ndata: {"phase": "generating"}\n\n` before the first `token` event

### Requirement: Frontend SHALL display phase status during chat

The chat view SHALL show a single-line status indicator below the last assistant message while streaming is in progress. The status text SHALL be visually distinct from normal message content.

#### Scenario: Show "Searching" during retrieval

- **WHEN** the frontend receives `event: phase\ndata: {"phase": "retrieving"}`
- **THEN** a status line reading `⏳ Searching...` SHALL appear below the assistant message area
- **AND** the line SHALL use italic font, muted gray color, and small font size

#### Scenario: Switch to "Generating" during generation

- **WHEN** the frontend receives `event: phase\ndata: {"phase": "generating"}`
- **THEN** the status line SHALL change to `✏️ Generating...`
- **AND** any previous status text SHALL be replaced, not appended

#### Scenario: Status disappears on completion

- **WHEN** the frontend receives the `done` event
- **THEN** the status line SHALL be removed
- **AND** no residual status text SHALL remain in the message list

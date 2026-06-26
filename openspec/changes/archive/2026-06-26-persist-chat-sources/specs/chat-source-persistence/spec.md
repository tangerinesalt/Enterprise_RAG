## ADDED Requirements

### Requirement: Persist sources in additional_kwargs
The streaming chat endpoint SHALL store the retrieved source documents in `ChatMessage.additional_kwargs` alongside the answer text.

#### Scenario: Sources persisted with assistant message
- **WHEN** `chat_stream()` finishes generating and persists to `SimpleChatStore`
- **THEN** the assistant `ChatMessage` SHALL have `additional_kwargs` containing `{"sources": [{"text": "...", "score": 0.92}]}`
- **THEN** the answer text SHALL remain unchanged in `content` (sources are NOT appended to text)

### Requirement: API returns sources in message list
The `GET /api/session/{name}/chats/{chat_file}` endpoint SHALL return `sources` as a top-level field in each message object, extracted from `additional_kwargs`.

#### Scenario: Sources field present
- **WHEN** a client calls `get_chat_messages()` for a chat that has streamed messages
- **THEN** each message object SHALL include a `sources` field: `{"role": "assistant", "content": "...", "sources": [{"text": "...", "score": 0.92}]}`
- **THEN** user messages SHALL have `sources: null`

#### Scenario: Legacy messages without sources
- **WHEN** a chat file was created by the synchronous `chat()` method (sources appended to content text)
- **THEN** the `sources` field SHALL be `null` in the API response
- **THEN** the frontend SHALL NOT display the collapsible sources section for such messages

### Requirement: Frontend sources display persists across chat switches
The frontend SHALL load `sources` from the API response when fetching chat messages, ensuring the collapsible "📎 来源" section is displayed after switching chats.

#### Scenario: Sources displayed after chat switch
- **WHEN** a user switches from Chat A (which has streamed messages with sources) to Chat B and back to Chat A
- **THEN** the collapsible "📎 来源" section SHALL still be visible on the same messages
- **THEN** the source text and score SHALL match the original values

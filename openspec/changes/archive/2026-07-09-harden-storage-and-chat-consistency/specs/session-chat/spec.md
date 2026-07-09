## MODIFIED Requirements

### Requirement: System SHALL persist chat history via SimpleChatStore

The system SHALL persist each conversation to a specific chat file via `SimpleChatStore`. When a request provides `chat_file`, the system SHALL load and append to that exact file instead of inferring the target from a session-global current chat. Both synchronous chat and streaming chat SHALL persist assistant messages using the same structured format, with assistant text in `content` and structured source citations in `additional_kwargs.sources`.

#### Scenario: Chat file creates per session
- **WHEN** user runs `session chat my-session "question"` for the first time without specifying `chat_file`
- **THEN** a new chat file is created at `sessions/my-session/chats/<timestamp>.json`
- **THEN** the file contains the user message and assistant response

#### Scenario: Chat continues on explicit chat file
- **WHEN** client sends `POST /api/session/chat` with `{"name": "my-session", "query": "follow-up", "chat_file": "2026_07_06_10_00.json"}`
- **THEN** the existing `SimpleChatStore` is loaded from `2026_07_06_10_00.json`
- **THEN** the new messages are appended to that same file
- **THEN** the assistant response uses that file's prior conversation context

#### Scenario: Explicit chat file ignores unrelated active chat metadata
- **WHEN** session metadata `active_chat` is `chat-b.json`
- **AND** client sends a request with `chat_file: "chat-a.json"`
- **THEN** the system appends the conversation to `chat-a.json`
- **THEN** it does NOT switch to `chat-b.json` because of session-global metadata

#### Scenario: Sync and stream chat persist identical assistant structure
- **WHEN** one assistant response is produced by `/api/session/chat` and another is produced by `/api/session/chat/stream`
- **THEN** both persisted assistant messages store answer text in `content`
- **THEN** both persisted assistant messages store structured citations in `additional_kwargs.sources`
- **THEN** history readers do not need different parsing logic for sync vs stream records

## ADDED Requirements

### Requirement: Hybrid retrieval SHALL refresh BM25 corpus after index content changes

The system SHALL ensure the BM25 side of hybrid retrieval is rebuilt or invalidated whenever the underlying indexed corpus changes, even if the total number of chunks remains unchanged.

#### Scenario: Reindex with unchanged chunk count refreshes BM25 corpus
- **WHEN** a file is reindexed and the resulting chunk count is the same as before but one or more chunk texts changed
- **THEN** subsequent hybrid retrieval uses the new BM25 corpus
- **THEN** stale chunk text from the previous index is not returned through BM25 cache reuse

#### Scenario: Query reuse within unchanged corpus may still use cache
- **WHEN** repeated queries run against a knowledge base whose indexed corpus has not changed
- **THEN** the system may reuse an in-process BM25 cache
- **THEN** the cache key reflects corpus identity rather than only collection size

### Requirement: History readers SHALL recover structured sources from persisted chat records

The system SHALL expose structured source information from persisted assistant messages so that history readers can reconstruct source panels without reparsing assistant text.

#### Scenario: Get messages returns persisted structured sources
- **WHEN** a persisted assistant message contains `additional_kwargs.sources`
- **THEN** history readers receive those sources as part of the chat message payload
- **THEN** source rendering does not depend on whether the chat was originally sync or streaming

#### Scenario: Legacy sync records degrade to body-only history
- **WHEN** a legacy persisted assistant message does not contain `additional_kwargs.sources`
- **THEN** history readers still receive the assistant `content`
- **THEN** the system does NOT synthesize structured sources by reparsing that legacy message body

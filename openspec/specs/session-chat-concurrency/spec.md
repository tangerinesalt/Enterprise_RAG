# session-chat-concurrency Specification

## Purpose
TBD - created by archiving change support-concurrent-chats-within-session. Update Purpose after archive.
## Requirements
### Requirement: System SHALL separate session-config and chat-file concurrency domains

The system SHALL protect session-level config state and chat-file state with separate lock domains instead of a single session-wide chat execution lock.

#### Scenario: Config update does not become the chat execution lock
- **WHEN** a request reads or updates `sessions/my-session/config.json`
- **THEN** the system uses the session-config lock for that shared file
- **THEN** it does NOT serialize all other chat execution in `my-session` for the full generation lifetime

#### Scenario: Chat persistence uses chat-file lock
- **WHEN** a request appends messages to `sessions/my-session/chats/2026_07_06_10_00.json`
- **THEN** the system uses the chat-file lock for that file
- **THEN** the lock scope is limited to the affected chat file

### Requirement: Different chat files within one session SHALL execute concurrently

The system SHALL allow chat requests targeting different `chat_file` values in the same session to run concurrently.

#### Scenario: Two pages chat on different files
- **WHEN** page A sends a chat request for `chat-a.json` in session `my-session`
- **AND** page B simultaneously sends a chat request for `chat-b.json` in the same session
- **THEN** both requests are allowed to progress without waiting for the other chat file to finish
- **THEN** each response is persisted only to its own chat file

#### Scenario: Stream and non-stream requests use different chat files
- **WHEN** one request uses `/api/session/chat/stream` for `chat-a.json`
- **AND** another request uses `/api/session/chat` for `chat-b.json`
- **THEN** the two requests do NOT block each other solely because they belong to the same session

### Requirement: The same chat file SHALL remain serialized

The system SHALL serialize mutation operations targeting the same `chat_file`.

#### Scenario: Same chat file receives two requests
- **WHEN** two requests target `sessions/my-session/chats/chat-a.json`
- **THEN** message persistence for that file is serialized
- **THEN** the file remains valid JSON
- **THEN** persisted messages do NOT interleave into a corrupted or lost-update state

### Requirement: Explicit chat targets SHALL remain stable under unrelated session-config writes

The system SHALL preserve an explicit `chat_file` target even when other operations mutate unrelated session config during the request lifetime.

#### Scenario: Update config during explicit chat request
- **WHEN** page A sends a chat request for `chat-a.json`
- **AND** another operation updates retrieval config for the same session while page A is still in progress
- **THEN** page A continues to read from and persist to `chat-a.json`
- **THEN** the config write does NOT redirect, cancel, or retarget the explicit chat request

### Requirement: Streaming requests SHALL include a traceable request_id

Each streaming chat request SHALL generate a unique `request_id` logged alongside every phase transition (token generated, error, done) for correlating concurrent requests.

#### Scenario: Concurrent request isolation
- **WHEN** two streaming requests run concurrently in the same session
- **THEN** each request has a unique `request_id`
- **THEN** the `request_id` is logged with each phase transition
- **THEN** tokens from request A are NOT mixed with tokens from request B

### Requirement: LLM client SHALL support concurrent streaming

If the global LLM client (httpx/requests session) is shared across streaming requests, it SHALL support concurrent response streams without data cross-contamination.

#### Scenario: Concurrent LLM streams
- **WHEN** two streaming LLM requests are sent concurrently through the same client
- **THEN** each stream receives only its own response data
- **THEN** one stream's completion does not interrupt the other

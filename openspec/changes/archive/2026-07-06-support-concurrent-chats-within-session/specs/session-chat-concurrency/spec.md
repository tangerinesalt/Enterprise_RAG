## ADDED Requirements

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

### Requirement: Shared active_chat metadata SHALL NOT gate explicit chat execution

The system SHALL treat `active_chat` as metadata only and SHALL NOT use it to block or redirect a request that explicitly specifies `chat_file`.

#### Scenario: active_chat changes during another page's request
- **WHEN** page A is chatting on `chat-a.json`
- **AND** page B changes session metadata so `active_chat` becomes `chat-b.json`
- **THEN** page A's in-flight or subsequent explicit requests for `chat-a.json` continue to use `chat-a.json`
- **THEN** they are NOT redirected, cancelled, or blocked by the metadata change

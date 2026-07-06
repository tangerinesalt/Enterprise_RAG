## MODIFIED Requirements

### Requirement: System SHALL persist chat history via SimpleChatStore

The system SHALL persist each conversation to a specific chat file via `SimpleChatStore`. When a request provides `chat_file`, the system SHALL load and append to that exact file instead of inferring the target from a session-global current chat.

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

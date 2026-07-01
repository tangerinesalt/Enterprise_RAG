## ADDED Requirements

### Requirement: Frontend SHALL show blank chat on session entry

When user enters a session page, the frontend SHALL display a blank chat area instead of automatically loading any existing chat history.

#### Scenario: Enter session with chats
- **WHEN** user navigates to `/session/<name>` and the session has existing chat files
- **THEN** the right panel shows the empty state prompt
- **THEN** the left sidebar lists all existing chat files
- **THEN** no API call is made to `GET /api/session/<name>/chats/<file>` on entry

#### Scenario: Enter session without chats
- **WHEN** user navigates to `/session/<name>` and the session has no chat files
- **THEN** the right panel shows the empty state prompt "点击「新聊天」开始对话"

### Requirement: Frontend SHALL create chat file on first submit

The chat file SHALL be created only when the user submits their first question, not when clicking "新聊天" or entering the session.

#### Scenario: Submit in blank state creates chat
- **WHEN** user is in blank chat state and submits a question
- **THEN** frontend calls `POST /api/session/new` to create a new chat file
- **THEN** frontend sends the question to `POST /api/session/chat/stream` with the new chat_file
- **THEN** after the stream completes, the activeChat state updates to the new filename

#### Scenario: Submit in existing chat appends
- **WHEN** user has selected an existing chat and submits a question
- **THEN** frontend sends directly to `POST /api/session/chat/stream` with the existing chat_file
- **THEN** no `POST /api/session/new` call is made

### Requirement: Frontend "新聊天" SHALL be client-side only

Clicking "新聊天" SHALL only clear the local state without making any API calls.

#### Scenario: New chat clears state
- **WHEN** user clicks "新聊天"
- **THEN** activeChat is set to null
- **THEN** messages are cleared
- **THEN** no API call to `POST /api/session/new` is made

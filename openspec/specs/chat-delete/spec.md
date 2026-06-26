# chat-delete Specification

## Purpose
TBD - created by archiving change session-chat-delete. Update Purpose after archive.
## Requirements
### Requirement: Delete chat API endpoint
The system SHALL provide a `DELETE /api/session/{name}/chats/{chat_file}` endpoint to delete a single chat within a session.

#### Scenario: Successful chat deletion
- **WHEN** a client sends `DELETE /api/session/光伏对话/chats/2026_06_25_15_53.json`
- **THEN** the server SHALL delete that chat file
- **THEN** the response SHALL be `{"ok": true, "data": {"name": "光伏对话", "chat_file": "2026_06_25_15_53.json"}}`

#### Scenario: Chat not found
- **WHEN** the chat file does not exist
- **THEN** the server SHALL return 404 with an error message

### Requirement: Frontend chat deletion UI
The session chat page SHALL provide a delete button on each chat entry in the left sidebar.

#### Scenario: Delete button visible
- **WHEN** the user views the chat list in a session
- **THEN** each chat entry SHALL have a 🗑️ delete button on the right

#### Scenario: Delete confirmation
- **WHEN** the user clicks the delete button
- **THEN** a confirmation dialog SHALL appear before deletion

#### Scenario: Chat list refresh after deletion
- **WHEN** a chat is deleted
- **THEN** the chat list SHALL refresh
- **THEN** if the deleted chat was active, the first remaining chat SHALL be selected
- **THEN** if no chats remain, the message area SHALL clear and show empty state


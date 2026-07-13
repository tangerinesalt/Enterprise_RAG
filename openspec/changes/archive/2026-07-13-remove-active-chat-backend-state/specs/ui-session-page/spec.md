## MODIFIED Requirements

### Requirement: Session chat page SHALL have two-column layout

The left column SHALL show session info, KB binding, retrieval parameter editing area, and chat list. The right column SHALL show the locally selected chat's messages and input.

#### Scenario: View session chat
- **WHEN** user clicks a session row
- **THEN** the left column shows session name, KB name, retrieval params area, new chat button, and chat list
- **THEN** the right column shows the locally selected chat's messages, or an empty state if no chat is selected yet
- **THEN** the input box is at the bottom of the right column

#### Scenario: Enter submits message
- **WHEN** user types a message and presses Enter
- **THEN** the message is sent via `POST /api/session/chat` or `POST /api/session/chat/stream`
- **THEN** the request includes the page's locally selected `chat_file`
- **THEN** the response is displayed in that same local chat view

#### Scenario: New chat
- **WHEN** user clicks "new chat" button
- **THEN** a new chat file is created via `POST /api/session/new`
- **THEN** the page locally selects the returned chat file
- **THEN** a blank chat area appears on the right
- **THEN** no request is sent to `/api/session/select`

#### Scenario: Switch chat
- **WHEN** user clicks a different chat in the left column list
- **THEN** the page updates its local selected `chat_file`
- **THEN** the right column loads and displays that chat's messages
- **THEN** no request is sent to `/api/session/select`

#### Scenario: Two pages keep different local selections
- **WHEN** page A selects `chat-a.json`
- **AND** page B selects `chat-b.json` in the same session
- **THEN** each page keeps and uses its own local selected chat
- **THEN** one page's selection does NOT forcibly replace the other page's current chat view

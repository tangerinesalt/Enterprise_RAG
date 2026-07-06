## Purpose

Define the React session pages for listing sessions, binding knowledge bases, switching chats, and sending messages.
## Requirements
### Requirement: Session list page SHALL show all sessions

The page SHALL display all sessions with bound KB info and create/delete.

#### Scenario: List sessions
- **WHEN** user visits `/session`
- **THEN** all sessions are listed with bound KB name and chat count

#### Scenario: Create session
- **WHEN** user clicks create button
- **THEN** a new session is created via `POST /api/session`

### Requirement: Session chat page SHALL have two-column layout

The left column SHALL show session info, KB binding, retrieval parameter editing area, and chat list. The right column SHALL show the locally selected chat's messages and input. The page SHALL keep the current selected `chat_file` in local page state instead of relying on a session-global authoritative active chat.

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
- **WHEN** user clicks "新聊天" button
- **THEN** a new chat file is created via `POST /api/session/new`
- **THEN** the page locally selects the returned chat file
- **THEN** a blank chat area appears on the right

#### Scenario: Switch chat
- **WHEN** user clicks a different chat in the left column list
- **THEN** the page updates its local selected `chat_file`
- **THEN** the right column loads and displays that chat's messages

#### Scenario: Two pages keep different local selections
- **WHEN** page A selects `chat-a.json`
- **AND** page B selects `chat-b.json` in the same session
- **THEN** each page keeps and uses its own local selected chat
- **THEN** one page's selection does NOT forcibly replace the other page's current chat view

### Requirement: User SHALL view and edit retrieval params in UI

The left column SHALL display a "检索参数" section below the KB binding area, showing current `top_k` and `top_n` with inline editing.

#### Scenario: Display current params
- **WHEN** user views the session chat page
- **THEN** the left column shows a "检索参数" section with `top_k` and `top_n` values
- **THEN** the values are displayed in editable number input fields

#### Scenario: Edit and save params
- **WHEN** user changes `top_k` or `top_n` values and clicks a save button
- **THEN** `PATCH /api/session/{name}/config` is called with the new values
- **THEN** on success, the inputs show the saved values with a brief "已保存" confirmation
- **THEN** on error, an error message is shown and inputs revert to previous values

#### Scenario: Validate params on save
- **WHEN** user enters 0 or negative values and clicks save
- **THEN** the save is rejected with a validation message "top_k 必须 ≥ 1"
- **THEN** the inputs are NOT sent to the API

### Requirement: Session chat page SHALL branch on structured stream errors

The frontend SHALL handle streaming chat errors using structured error fields from the API instead of parsing free-form error text.

#### Scenario: KB error uses structured category
- **WHEN** the stream returns an `error` event with `category = "kb"`
- **THEN** the page shows the KB-specific warning flow
- **THEN** the page does NOT need to infer that flow from Chinese text fragments

#### Scenario: Model error uses structured category
- **WHEN** the stream returns an `error` event with `category = "model"` or a model-related `code`
- **THEN** the page shows the model-loading warning flow
- **THEN** the page does NOT need to inspect provider names such as `Ollama` in the message text

#### Scenario: Generic runtime error still shows message
- **WHEN** the stream returns an `error` event with an unknown `code`
- **THEN** the page still renders the returned `message` in the assistant placeholder
- **THEN** the chat remains reloadable from persisted history


## MODIFIED Requirements

### Requirement: Session chat page SHALL have two-column layout

The left column SHALL show session info, KB binding, retrieval parameter editing area, and chat list. The right column SHALL show messages and input.

#### Scenario: View session chat
- **WHEN** user clicks a session row
- **THEN** the left column shows session name, KB name (or bind button), retrieval params area, new chat button, chat list
- **THEN** the right column shows the active chat's messages
- **THEN** the input box is at the bottom of the right column

#### Scenario: Enter submits message
- **WHEN** user types a message and presses Enter
- **THEN** the message is sent via `POST /api/session/chat`
- **THEN** the response is displayed in the chat

#### Scenario: Shift+Enter adds newline
- **WHEN** user presses Shift+Enter in the input
- **THEN** a newline is inserted instead of submitting

#### Scenario: New chat
- **WHEN** user clicks "新聊天" button
- **THEN** a new chat file is created via `POST /api/session/new`
- **THEN** a blank chat area appears on the right

#### Scenario: Switch chat
- **WHEN** user clicks a different chat in the left column list
- **THEN** the right column loads and displays that chat's messages

## ADDED Requirements

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

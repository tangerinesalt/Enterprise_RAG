## MODIFIED Requirements

### Requirement: Session chat page SHALL have two-column layout

The left column SHALL show session info, KB binding, retrieval parameter editing area, and chat list. The right column SHALL show messages, input, and failed-turn feedback for the active chat.

#### Scenario: View session chat
- **WHEN** user clicks a session row
- **THEN** the left column shows session name, KB name (or bind button), retrieval params area, new chat button, chat list
- **THEN** the right column shows the active chat's messages
- **THEN** the input box is at the bottom of the right column

#### Scenario: Enter submits message
- **WHEN** user types a message and presses Enter
- **THEN** the message is sent via `POST /api/session/chat/stream`
- **THEN** the streaming response is displayed in the chat

#### Scenario: Shift+Enter adds newline
- **WHEN** user presses Shift+Enter in the input
- **THEN** a newline is inserted instead of submitting

#### Scenario: New chat
- **WHEN** user clicks "鏂拌亰澶? button
- **THEN** a new chat file is created via `POST /api/session/new`
- **THEN** a blank chat area appears on the right

#### Scenario: Switch chat
- **WHEN** user clicks a different chat in the left column list
- **THEN** the right column loads and displays that chat's messages

#### Scenario: Failed first turn remains visible
- **WHEN** the first request in a newly created chat fails after the chat execution flow starts
- **THEN** the chat remains in the left column list
- **THEN** reopening the chat shows the user's question and the assistant error message

## ADDED Requirements

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

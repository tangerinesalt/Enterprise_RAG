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

The left column SHALL show session info, KB binding, and chat list. The right column SHALL show messages and input.

#### Scenario: View session chat
- **WHEN** user clicks a session row
- **THEN** the left column shows session name, KB name (or bind button), new chat button, chat list
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
- **WHEN** user clicks "鏂拌亰澶? button
- **THEN** a new chat file is created via `POST /api/session/new`
- **THEN** a blank chat area appears on the right

#### Scenario: Switch chat
- **WHEN** user clicks a different chat in the left column list
- **THEN** the right column loads and displays that chat's messages

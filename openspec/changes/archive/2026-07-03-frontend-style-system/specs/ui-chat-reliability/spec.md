## ADDED Requirements

### Requirement: SSE stream is cancellable

When the user sends a new chat message while a previous streaming response is still in progress, the previous stream SHALL be aborted before starting the new one. Switching chats during an active stream SHALL also abort the stream.

#### Scenario: Rapid consecutive sends

- **WHEN** user sends message A (streaming starts)
- **WHEN** user sends message B before A finishes
- **THEN** stream A is aborted
- **THEN** only stream B's tokens appear in the assistant message
- **THEN** the final message content matches only stream B's response

#### Scenario: Switch chat mid-stream

- **WHEN** user sends a message (stream starts)
- **WHEN** user clicks a different chat in the sidebar before the stream ends
- **THEN** the original stream is aborted
- **THEN** the new chat's messages are loaded
- **THEN** no residual tokens from the aborted stream appear in any message

### Requirement: Chat delete does not reference stale state

After deleting a chat, the next active chat selection SHALL be computed from the fresh server response, not from locally cached state.

#### Scenario: Delete last chat in list

- **WHEN** there is exactly 1 chat in the list
- **WHEN** user deletes that chat
- **THEN** the chat list becomes empty
- **THEN** `activeChat` is set to null
- **THEN** the message area shows the empty-state placeholder

#### Scenario: Delete non-last chat

- **WHEN** there are 3 chats and the first one is active
- **WHEN** user deletes the active chat
- **THEN** the next available chat becomes active
- **THEN** that chat's messages are loaded

### Requirement: Unhandled render errors show fallback UI

If any component throws during rendering, the user SHALL see an error fallback page with a "重新加载" button instead of a white screen.

#### Scenario: Catastrophic render error

- **WHEN** a React component throws an exception during render
- **THEN** ErrorBoundary catches the error
- **THEN** a centered error message is displayed
- **THEN** a button labeled "重新加载" reloads the page

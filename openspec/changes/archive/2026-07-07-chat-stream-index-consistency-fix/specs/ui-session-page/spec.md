## MODIFIED Requirements

### Requirement: Session chat page SHALL cancel stream on chat switch and deletion

Local chat-view change operations (switch chat, delete current chat) SHALL trigger stream cancellation before mutating local selection state. The page SHALL maintain the invariant of at most one active stream per page — stale streams SHALL NOT continue writing to the UI after the page target changes.

#### Scenario: Switch chat — cancel before state change

- **WHEN** the user clicks a different chat in the sidebar while a streaming response is in progress
- **THEN** the cancellation is triggered before `selectedChatFile` state updates
- **THEN** the page resets `loading` to `false`
- **THEN** the local selection switches to the target chat
- **THEN** the target chat's messages load without modification from stale data

#### Scenario: Delete current chat — cancel before view replacement

- **WHEN** the user deletes the currently selected chat while a streaming response is in progress
- **THEN** the cancellation is triggered before the chat deletion
- **THEN** the page resets `loading` to `false`
- **THEN** the chat is deleted and the page shows an empty state or the next available chat
- **THEN** stale stream tokens do not accidentally render in the post-deletion UI

#### Scenario: New chat available after current stream is cancelled

- **WHEN** a stream was already started before cancellation
- **THEN** page state recovers cleanly after cancellation
- **THEN** the user can switch between chats without refreshing the page
- **THEN** the switch does not leave behind partially-appended message content

## MODIFIED Requirements

### Requirement: System SHALL cancel in-flight stream when chat target changes

When the local chat target changes (switch chat or delete current chat), the system (frontend stream lifecycle layer) SHALL cancel any in-flight streaming response to prevent stale tokens from writing into the wrong chat view. This operation SHALL be a no-op if no stream is currently active.

#### Scenario: Cancel stream on chat switch

- **WHEN** the user clicks a different chat in the sidebar while a streaming response is in progress
- **THEN** the page's local `AbortController` is triggered to cancel the in-flight stream
- **THEN** the local selection switches to the new target chat
- **THEN** no stale tokens from the cancelled stream are appended to the new chat view
- **THEN** the new chat view is in a normal ready state

#### Scenario: Cancel stream on current-chat deletion

- **WHEN** the user deletes the currently selected chat while a streaming response is in progress
- **THEN** the page's local `AbortController` is triggered to cancel the in-flight stream
- **THEN** the chat is deleted and the page selects a replacement view or shows an empty state
- **THEN** no stale tokens from the cancelled stream appear in the post-deletion UI

#### Scenario: Sending new message cancels stream (unchanged)

- **WHEN** the user sends a new message while a streaming response is in progress (existing behavior unchanged)
- **THEN** the existing stream is cancelled (same as current logic)
- **THEN** the new message is dispatched normally

#### Scenario: No-op when no active stream

- **WHEN** the user switches chats while no stream is active
- **THEN** the cancellation is safely ignored
- **THEN** the chat view switches normally with no error

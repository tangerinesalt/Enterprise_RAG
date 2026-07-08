## ADDED Requirements

### Requirement: Streaming chat SHALL tolerate client-side cancellation without cross-chat leakage

The system SHALL ensure that a streaming chat request only mutates the target chat view it was started for. Once the client cancels the stream because the local chat target changed, no additional streamed output from that request shall be applied to a different chat view.

#### Scenario: Switching chats stops obsolete stream updates
- **WHEN** the client starts a streaming chat for `chat-a.json`
- **AND** the user switches the local selection to `chat-b.json` before the stream completes
- **THEN** the in-flight stream is cancelled
- **THEN** no further tokens from the cancelled request are applied to the `chat-b.json` view

#### Scenario: Deleting current chat stops obsolete stream updates
- **WHEN** the client starts a streaming chat for the currently selected chat
- **AND** the user deletes that current chat before the stream completes
- **THEN** the in-flight stream is cancelled
- **THEN** no further tokens from the cancelled request are applied to the replacement view or empty state

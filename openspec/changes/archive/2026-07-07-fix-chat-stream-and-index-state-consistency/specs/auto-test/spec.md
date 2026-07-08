## ADDED Requirements

### Requirement: Automated tests SHALL cover chat stream cancellation boundaries

The automated regression suite SHALL verify that local chat-target changes cancel obsolete streaming chat work before it can contaminate another chat view.

#### Scenario: Switching chats cancels obsolete stream
- **WHEN** an automated test starts a streaming chat for one local chat target and then switches the local selection before completion
- **THEN** the obsolete stream is cancelled
- **THEN** late output from the cancelled request is not applied to the newly selected chat view

#### Scenario: Deleting current chat cancels obsolete stream
- **WHEN** an automated test starts a streaming chat for the currently selected chat and then deletes that chat before completion
- **THEN** the obsolete stream is cancelled
- **THEN** late output from the cancelled request is not applied to the replacement view or empty state

### Requirement: Automated tests SHALL cover KB index-state consistency

The automated regression suite SHALL verify that KB indexing status semantics stay consistent across sync and stream paths and that failure paths do not leave stale progress state assumptions.

#### Scenario: Sync and stream indexing persist matching file status semantics
- **WHEN** automated tests index the same file through synchronous and streaming KB indexing paths
- **THEN** both paths persist the same file-level `indexed` status meaning
- **THEN** both paths persist file-scoped chunk counts instead of collection-wide totals

#### Scenario: KB indexing failure handling remains recoverable
- **WHEN** an automated test simulates a KB indexing failure after local progress has started
- **THEN** the resulting observable state remains recoverable for the next indexing attempt
- **THEN** the failure does not require manual cleanup of stale in-progress state assumptions

## REMOVED Requirements

### Requirement: Shared active_chat metadata SHALL NOT gate explicit chat execution
**Reason**: The system no longer maintains shared `active_chat` metadata at all.
**Migration**: Concurrency guarantees MUST be expressed only in terms of explicit `chat_file` targets and unrelated session-config writes.

## ADDED Requirements

### Requirement: Explicit chat targets SHALL remain stable under unrelated session-config writes

The system SHALL preserve an explicit `chat_file` target even when other operations mutate unrelated session config during the request lifetime.

#### Scenario: Update config during explicit chat request
- **WHEN** page A sends a chat request for `chat-a.json`
- **AND** another operation updates retrieval config for the same session while page A is still in progress
- **THEN** page A continues to read from and persist to `chat-a.json`
- **THEN** the config write does NOT redirect, cancel, or retarget the explicit chat request

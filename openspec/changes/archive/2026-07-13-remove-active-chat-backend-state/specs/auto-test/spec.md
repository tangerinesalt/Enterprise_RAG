## MODIFIED Requirements

### Requirement: Automated tests SHALL cover same-session chat concurrency boundaries

The system SHALL provide automated tests that verify concurrent behavior within the same session across different chat files, while preserving serialization for the same chat file.

#### Scenario: Different chat files can run concurrently
- **WHEN** an automated test starts two chat requests in the same session with different `chat_file` values
- **THEN** both requests complete without one being forced to wait for the entire other request lifecycle
- **THEN** each chat file contains only its own conversation messages

#### Scenario: Same chat file remains serialized
- **WHEN** an automated test starts two requests against the same `chat_file`
- **THEN** persistence remains serialized for that file
- **THEN** the final chat file stays valid and message history is not corrupted

#### Scenario: Explicit chat file is stable under unrelated config writes
- **WHEN** an automated test updates session config while another request continues on an explicit `chat_file`
- **THEN** the explicit chat request continues to persist to its original target file
- **THEN** it is not redirected or retargeted by the config write

## ADDED Requirements

### Requirement: Automated tests SHALL cover full removal of the active-chat backend contract

The regression suite SHALL verify that no supported backend surface still depends on or exposes active-chat selection metadata.

#### Scenario: Session APIs no longer expose active-chat fields
- **WHEN** an automated test fetches session detail, session list, and chat list responses after the change
- **THEN** no response payload contains `active_chat`
- **THEN** no chat list entry contains `is_active`

#### Scenario: Removed selection endpoint is unsupported
- **WHEN** an automated test sends a request to `POST /api/session/select`
- **THEN** the request fails as an unsupported route

#### Scenario: Legacy config with active_chat is cleaned on rewrite
- **WHEN** an automated test seeds a legacy `config.json` containing `active_chat`
- **THEN** the session manager can still load and use the session
- **THEN** after a supported config write, the persisted file no longer contains `active_chat`

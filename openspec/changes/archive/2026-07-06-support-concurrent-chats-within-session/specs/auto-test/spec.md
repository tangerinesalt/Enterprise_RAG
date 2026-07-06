## ADDED Requirements

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

#### Scenario: Explicit chat file is stable under metadata changes
- **WHEN** an automated test changes session metadata such as `active_chat` while another request continues on an explicit `chat_file`
- **THEN** the explicit chat request continues to persist to its original target file
- **THEN** it is not redirected by the metadata update

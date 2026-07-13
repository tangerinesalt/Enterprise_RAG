## MODIFIED Requirements

### Requirement: Session storage SHALL serialize writes per session

The system SHALL serialize config-file writes and chat-file writes within the same session so that concurrent operations do not silently overwrite each other's updates.

#### Scenario: Concurrent chat and config update on same session
- **WHEN** one request is persisting chat content for session `demo` while another request updates `demo/config.json`
- **THEN** the writes are executed in a deterministic serialized order within session `demo`
- **THEN** the final `config.json` and chat file both remain valid JSON
- **THEN** the completed write from each operation is preserved instead of being partially lost

#### Scenario: Writes for different sessions do not block each other
- **WHEN** session `a` and session `b` both receive write operations at the same time
- **THEN** serialization is applied independently per session
- **THEN** an operation on session `a` does NOT require waiting for an unrelated write on session `b`

#### Scenario: All session-mutating paths share the same serialization boundary
- **WHEN** the system performs `new_chat`, `delete(chat_file)`, `update_config`, `chat()`, or `chat_stream()` for the same session
- **THEN** each operation participates in the same per-session serialization strategy
- **THEN** no write path bypasses the session safety guarantee by writing files directly outside that boundary

### Requirement: Session config SHALL be persisted atomically

The system SHALL persist `sessions/<name>/config.json` using an atomic replace strategy.

#### Scenario: Config update does not leave partial file
- **WHEN** the system updates `sessions/demo/config.json`
- **THEN** the new content is written to a temporary file before replacing the old file
- **THEN** observers never see a partially written `config.json`

#### Scenario: Preview update and config cleanup share atomic config write
- **WHEN** the system updates `chat_previews` or rewrites legacy config fields for the same session
- **THEN** the resulting `config.json` is committed through the same atomic persistence path
- **THEN** the resulting file contains a single valid snapshot without resurrecting removed fields such as `active_chat`

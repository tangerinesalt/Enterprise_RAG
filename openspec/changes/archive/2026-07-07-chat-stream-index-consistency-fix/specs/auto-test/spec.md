## ADDED Requirements

### Requirement: Regression tests SHALL cover chat stream cancellation at API level

The automated regression test suite SHALL verify that a cancelled streaming chat request does not produce observable side effects on the server. Tests SHALL use FastAPI TestClient with a monkeypatched session layer to simulate cancellation. Frontend-level verification (UI state cleanup after cancel) SHALL be done manually.

#### Scenario: Cancelled stream does not append messages to target chat

- **WHEN** an automated test starts a streaming chat request via `POST /api/session/chat/stream`
- **AND** the test closes the HTTP connection before the stream completes (simulating client-side abort)
- **THEN** the target chat file on disk does not contain partial or corrupted message content from the cancelled stream
- **THEN** subsequent requests to the same chat file return valid, uncorrupted history

#### Scenario: Cancelled stream does not block subsequent chat operations

- **WHEN** a streaming chat request is cancelled mid-flight via connection close
- **THEN** a new chat request to the same session and chat file succeeds without stale lock contention
- **THEN** the resulting chat file contains only the completed request's data

### Requirement: Regression tests SHALL cover KB indexing failure state via status file

The automated regression test suite SHALL verify that KB indexing failures produce correct state in the persisted `.index_status.json` file. Tests SHALL use real or mocked `Indexer` calls through the API router layer. Frontend progress-indicator cleanup SHALL be verified manually.

#### Scenario: Index failure leaves status file correct

- **WHEN** an automated test triggers an index request that fails partway (simulated via `Indexer` or mock)
- **THEN** the `.index_status.json` file for the KB does not indicate "in progress" for any file
- **THEN** each file's status is either `"pending"` or `"indexed"` with the correct error semantics
- **THEN** the status file remains valid JSON and is readable by subsequent operations

#### Scenario: Sync and stream failure produce consistent status file state

- **WHEN** a synchronous index request fails for a file
- **AND** a streaming index request fails for a comparable file
- **THEN** the resulting entry in `.index_status.json` follows the same schema and semantics in both cases
- **THEN** neither leaves a dangling "in progress" entry

### Requirement: Regression tests SHALL verify sync and stream index status consistency

The automated regression test suite SHALL verify that synchronous indexing and streaming indexing produce the same persisted file status semantics (`indexed`/`chunks`) for the same set of files.

#### Scenario: Sync and stream indexing produce matching file status

- **WHEN** an automated test indexes a set of files using the sync path and records the resulting file status
- **AND** the test indexes another set of files with the same characteristics using the stream path and records the resulting file status
- **THEN** the `indexed` status for both sets has the same semantics (indicates a specific file succeeded)
- **THEN** the `chunks` values in both sets reflect file-level chunk counts, not collection-wide totals
- **THEN** the persisted status file schema is consistent across both paths

#### Scenario: Sync index writes correct file-level chunk count

- **WHEN** an automated test indexes a single file with known document content using the sync path
- **THEN** the persisted status shows `chunks` equal to `len(nodes)` — the number of nodes produced by that document
- **THEN** `chunks` is NOT equal to the entire collection's `collection.count()`
- **THEN** `set_file_status(..., "indexed", chunks=...)` was called during the sync index

#### Scenario: Stream index writes correct file-level chunk count

- **WHEN** an automated test indexes a single file using the stream path
- **THEN** the `index_done` SSE event carries `chunks=len(nodes)` (not `collection.count()`)
- **THEN** the persisted status file shows the same `chunks` value as the sync path would produce for the same file

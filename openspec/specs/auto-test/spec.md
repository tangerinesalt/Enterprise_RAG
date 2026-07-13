## Purpose

Define automated test specifications for end-to-end CLI workflow validation, including upload, index, query, and delete operations.
## Requirements
### Requirement: Test script SHALL validate end-to-end CLI workflow

The system SHALL provide `test/test_auto.py` that creates test data and verifies upload → index → query → delete.

#### Scenario: Full workflow test
- **WHEN** `python test/test_auto.py` is run
- **THEN** a test directory is created on the desktop at `rag-test/`
- **THEN** test files are created covering A1, A2, A3, A4 topics
- **THEN** a knowledge base is created and the folder is uploaded
- **THEN** the folder is indexed
- **THEN** each topic (A1-A4) is queried
- **THEN** each response is verified to contain expected keywords
- **THEN** the knowledge base is cleaned up (files + vectors deleted)
- **THEN** the desktop test directory is deleted
- **THEN** a pass/fail report is printed

#### Scenario: Test data layout
- **WHEN** the test runs
- **THEN** `%USERPROFILE%/Desktop/rag-test/` contains:
  - `A1-概述.txt` with content answering "什么是A1？"
  - `A2-原理.txt` with content answering "什么是A2？"
  - `sub/A3-应用.txt` with content answering "什么是A3？"
  - `sub/A4-实践.txt` with content answering "什么是A4？"

#### Scenario: Retrieval diagnostic runs after indexing
- **WHEN** indexing completes
- **THEN** `test_retrieval_diagnostic.py` is called as a subprocess with the test KB and query
- **THEN** diagnostic output is checked for anomalies E01 and E03
- **THEN** if either anomaly is detected, a WARNING is printed (test does not fail)

### Requirement: Reliability regression suite SHALL cover chat failure persistence

The automated regression suite SHALL verify that both synchronous and streaming chat preserve the failed turn once chat execution has started.

#### Scenario: Sync chat failed turn is preserved
- **WHEN** an automated test triggers `POST /api/session/chat` and the request fails after the target chat file is determined
- **THEN** the resulting chat history contains the user question
- **THEN** the resulting chat history contains an assistant error message

#### Scenario: Stream chat failed turn is preserved
- **WHEN** an automated test triggers `POST /api/session/chat/stream` and the request fails after the target chat file is determined
- **THEN** the resulting chat history contains the user question
- **THEN** the resulting chat history contains an assistant error message

### Requirement: Reliability regression suite SHALL cover structured stream errors

The automated regression suite SHALL verify the structured SSE error contract for streaming chat.

#### Scenario: Stream error payload includes stable fields
- **WHEN** an automated test triggers a streaming chat failure
- **THEN** the observed `error` event payload includes `code`
- **THEN** the observed `error` event payload includes `category`
- **THEN** the observed `error` event payload includes `message`

### Requirement: Reliability regression suite SHALL cover session write safety

The automated regression suite SHALL verify that concurrent writes on the same session do not leave invalid or partially overwritten session state.

#### Scenario: Concurrent session writes keep valid state
- **WHEN** an automated test performs concurrent write operations against the same session
- **THEN** the final `config.json` remains valid JSON
- **THEN** the final chat file remains valid JSON
- **THEN** the final state preserves the completed write from each operation's critical fields

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

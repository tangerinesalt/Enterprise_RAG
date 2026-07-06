## ADDED Requirements

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

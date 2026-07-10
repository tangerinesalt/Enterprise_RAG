# chat-stream-graceful-shutdown Specification

## Purpose
TBD - created by archiving change chat-stream-abort-deadlock. Update Purpose after archive.
## Requirements
### Requirement: Server SHALL disconnect streaming generators on client abort

When a client disconnects during a streaming chat response (SSE), the server SHALL close the LLM response generator and release all locks within a bounded time to prevent resource leaks.

#### Scenario: Client disconnects mid-stream
- **WHEN** client aborts a streaming chat request during token generation
- **THEN** the server detects the disconnection via `GeneratorExit`
- **THEN** the server closes the LLM `response.response_gen` iterator
- **THEN** the server releases the `_chat_file_lock` within 1 second
- **THEN** the chat store retains the user message (normal behavior for submitted queries)
- **THEN** subsequent operations on the same chat file work normally

#### Scenario: Repeated stream abort does not degrade performance
- **WHEN** a user repeatedly starts and aborts streaming requests (5 times within 10 seconds)
- **THEN** each abort is handled independently
- **THEN** no cumulative resource leak occurs
- **THEN** subsequent streaming requests complete normally

### Requirement: Router SHALL detect disconnected clients

The streaming route SHALL check `request.is_disconnected` before each SSE event yield and exit early if the client is gone.

#### Scenario: Early exit on disconnect
- **WHEN** client disconnects during the streaming response
- **THEN** the router exits the generator loop before the next yield
- **THEN** the `StreamingResponse` cleanly terminates


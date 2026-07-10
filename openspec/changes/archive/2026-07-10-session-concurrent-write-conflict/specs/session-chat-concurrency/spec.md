## ADDED Requirements

### Requirement: Streaming requests SHALL include a traceable request_id

Each streaming chat request SHALL generate a unique `request_id` logged alongside every phase transition (token generated, error, done) for correlating concurrent requests.

#### Scenario: Concurrent request isolation
- **WHEN** two streaming requests run concurrently in the same session
- **THEN** each request has a unique `request_id`
- **THEN** the `request_id` is logged with each phase transition
- **THEN** tokens from request A are NOT mixed with tokens from request B

### Requirement: LLM client SHALL support concurrent streaming

If the global LLM client (httpx/requests session) is shared across streaming requests, it SHALL support concurrent response streams without data cross-contamination.

#### Scenario: Concurrent LLM streams
- **WHEN** two streaming LLM requests are sent concurrently through the same client
- **THEN** each stream receives only its own response data
- **THEN** one stream's completion does not interrupt the other

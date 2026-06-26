## ADDED Requirements

### Requirement: System SHALL log request timing automatically

Every HTTP request SHALL be logged with its processing time.

#### Scenario: Request logged
- **WHEN** client sends `GET /api/kb`
- **THEN** the terminal prints `[TIMING] GET /api/kb → 0.003s`

#### Scenario: Slow request warning
- **WHEN** a request takes more than 1 second
- **THEN** the log message includes a WARN indicator

### Requirement: System SHALL track Ollama call timing

Ollama Embedding and Chat calls SHALL be individually timed.

#### Scenario: Embedding timed
- **WHEN** `embed_texts()` is called
- **THEN** the elapsed time is logged with label `ollama_embed`

### Requirement: API SHALL provide performance endpoint

The system SHALL expose `GET /api/performance` returning recent request timings.

#### Scenario: Get performance data
- **WHEN** client sends `GET /api/performance`
- **THEN** response includes list of recent requests with method, path, and elapsed time

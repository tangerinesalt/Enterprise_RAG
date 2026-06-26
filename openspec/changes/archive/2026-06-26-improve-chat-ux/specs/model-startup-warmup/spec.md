## ADDED Requirements

### Requirement: Model initialization at server startup
The system SHALL initialize LLM and Embedding models during FastAPI server startup, before the first HTTP request is accepted.

#### Scenario: Models warm on first request
- **WHEN** the FastAPI server starts
- **THEN** `init_models()` SHALL be called during the `lifespan` startup phase
- **THEN** the first chat request SHALL NOT trigger a cold `init_models()` call

#### Scenario: Idempotent initialization
- **WHEN** the lifespan calls `init_models()` at startup
- **THEN** subsequent calls to `init_models()` (e.g., from `SessionManager.chat()`) SHALL be no-ops due to the existing thread lock guard
- **THEN** the existing `_ensure_models_initialized()` guard in `SessionManager` SHALL remain as a fallback

#### Scenario: Graceful failure
- **WHEN** model initialization fails during startup (e.g., Ollama not reachable)
- **THEN** the server SHALL still start successfully (not crash)
- **THEN** a warning SHALL be logged
- **THEN** the first chat request SHALL attempt initialization as before (existing fallback behavior)

### Requirement: Timing decorator on lifecycle init
The system SHALL log the duration of startup model initialization.

#### Scenario: Startup timing logged
- **WHEN** the server starts and `init_models()` runs
- **THEN** the elapsed time SHALL be printed in the standard `[TIMING]` format

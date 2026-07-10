## Requirements

### Requirement: User SHALL view and edit retrieval params in UI

The left column SHALL display a combined "retrieval params" card below the KB selector, showing `top_k`, `top_n`, and system prompt with a single save button.

#### Scenario: Display combined config card
- **WHEN** user views the session chat page
- **THEN** the left column shows a card containing `top_k` and `top_n` number inputs, a system prompt textarea, and a "save all config" button

#### Scenario: Edit and save all params
- **WHEN** user changes `top_k`, `top_n` or system prompt and clicks "save all config"
- **THEN** `PATCH /api/session/{name}/config` is called with all three values (`top_k`, `top_n`, `system_prompt`)
- **THEN** on success, a brief "saved" confirmation appears
- **THEN** on error, an error message is shown

#### Scenario: Validate params on save
- **WHEN** user enters 0 or negative values for `top_k` or `top_n` and clicks save
- **THEN** the save is rejected with a validation message "top_k must be >= 1"
- **THEN** the inputs are NOT sent to the API

### Requirement: System prompt SHALL be saved with retrieval params

The system prompt textarea SHALL be part of the same card as retrieval params, and saved via the same save action.

#### Scenario: Save system prompt
- **WHEN** user edits the system prompt textarea and clicks "save all config"
- **THEN** the prompt is included in the PATCH request as `system_prompt`
- **THEN** on success, the saved prompt persists on reload

### Requirement: Session SHALL persist retrieval parameters in config

The session config.json SHALL store `top_k` and `top_n` fields controlling retrieval behavior.

#### Scenario: Default values on create
- **WHEN** a new session is created via CLI `session create my-session` or API `POST /api/session`
- **THEN** `sessions/my-session/config.json` contains `"top_k": 8` and `"top_n": 5`
- **THEN** these values are written at creation time

#### Scenario: Missing fields fall back to defaults
- **WHEN** an existing session config.json lacks `top_k` or `top_n` fields
- **THEN** the system uses `top_k=8` and `top_n=5` as implicit defaults
- **THEN** the config file is NOT modified by a read-only operation

### Requirement: User SHALL view retrieval parameters

The system SHALL display the current `top_k` and `top_n` values for a session.

#### Scenario: CLI show config
- **WHEN** user runs `session config my-session`
- **THEN** output shows `top_k: 8` and `top_n: 5` (or current values)

#### Scenario: API show config
- **WHEN** client sends `GET /api/session/my-session`
- **THEN** response includes `"top_k": 8` and `"top_n": 5` in the session info

### Requirement: User SHALL modify retrieval parameters

The system SHALL allow updating `top_k` and `top_n` per session.

#### Scenario: CLI modify single param
- **WHEN** user runs `session config my-session --set top_k=10`
- **THEN** config.json is updated with `"top_k": 10`
- **THEN** `top_n` remains unchanged

#### Scenario: CLI modify both params
- **WHEN** user runs `session config my-session --set top_k=10 --set top_n=7`
- **THEN** config.json is updated with `"top_k": 10, "top_n": 7`

#### Scenario: API modify config
- **WHEN** client sends `PATCH /api/session/my-session/config` with `{"top_k": 12}`
- **THEN** config.json is updated with `"top_k": 12`
- **THEN** only the specified fields are changed

#### Scenario: Reject invalid values
- **WHEN** user attempts to set `top_k=0` or `top_n=-1` via CLI or API
- **THEN** the system rejects with an error message: `top_k MUST be >= 1`
- **THEN** config.json is NOT modified

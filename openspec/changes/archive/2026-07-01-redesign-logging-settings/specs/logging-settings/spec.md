## ADDED Requirements

### Requirement: Runtime logging SHALL be quiet by default
The system SHALL avoid emitting routine successful request timing logs during normal backend and frontend runtime.

#### Scenario: Successful backend request produces no application timing log
- **WHEN** a client sends a successful `GET /api/kb` request in default logging mode
- **THEN** the application does not emit a `[TIMING]` log for that request

#### Scenario: Successful frontend request produces no browser timing log
- **WHEN** the frontend successfully calls `GET /api/session` in default logging mode
- **THEN** the browser console does not emit a `[API]` or `[API][SLOW]` timing message

### Requirement: Runtime errors SHALL remain visible
The system SHALL emit runtime errors through the appropriate backend stderr/logger or browser console channel even when debug logging is disabled.

#### Scenario: Backend startup model initialization fails
- **WHEN** backend model initialization fails during application startup
- **THEN** the backend emits an error log containing the failure message

#### Scenario: Frontend API request fails
- **WHEN** a frontend API request fails because the backend returns an error or the network request fails
- **THEN** the browser console emits an error message for that failed request

### Requirement: Debug request logs SHALL be opt-in
The system SHALL provide an explicit local configuration switch for verbose request/debug logs.

#### Scenario: Frontend debug flag enables request logs
- **WHEN** the frontend debug logging flag is enabled
- **THEN** successful frontend API calls may emit request method, path, and elapsed time to the browser console

#### Scenario: Backend debug flag enables application debug logs
- **WHEN** backend debug logging is enabled
- **THEN** backend application debug logs may include additional request or workflow details

### Requirement: Log destinations SHALL be documented
The project documentation SHALL define where developers should look for backend process logs, frontend process logs, browser console logs, and retrieval diagnostic reports.

#### Scenario: Developer follows log route documentation
- **WHEN** a developer needs to debug a local frontend issue
- **THEN** documentation identifies the browser console, browser network panel, and `logs/dev-frontend.*.log` as relevant locations

#### Scenario: Developer follows backend log documentation
- **WHEN** a developer needs to debug a backend startup or API issue
- **THEN** documentation identifies the backend terminal or `logs/dev-backend.*.log` as relevant locations

### Requirement: Retrieval diagnostics SHALL remain explicit tools
Detailed retrieval pipeline diagnostics SHALL only be produced by explicit diagnostic commands or scripts, not by normal chat requests.

#### Scenario: Normal chat request
- **WHEN** a user sends a chat request through the frontend or API
- **THEN** the backend does not emit stage-by-stage retrieval diagnostic output by default

#### Scenario: Diagnostic command
- **WHEN** a developer runs `python test/test_retrieval_diagnostic.py <kb_name> "<query>"`
- **THEN** the diagnostic script prints stage-by-stage retrieval details and writes its JSON report as specified by the retrieval diagnostic capability

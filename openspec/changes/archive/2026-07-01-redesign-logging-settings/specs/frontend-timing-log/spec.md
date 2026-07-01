## MODIFIED Requirements

### Requirement: Frontend SHALL log API request timing
The frontend API wrapper SHALL only record and print successful request timing to the browser console when frontend debug logging is explicitly enabled.

#### Scenario: API call not logged by default
- **WHEN** frontend calls `GET /api/session` with debug logging disabled
- **THEN** browser console does not show a successful request timing message

#### Scenario: API call logged when debug logging enabled
- **WHEN** frontend calls `GET /api/session` with debug logging enabled
- **THEN** browser console shows request method, path, and elapsed time

#### Scenario: Slow request warning when debug logging enabled
- **WHEN** a request takes more than 1 second and debug logging is enabled
- **THEN** console shows a slow request warning with the elapsed time

#### Scenario: Failed request remains visible
- **WHEN** a frontend API request fails
- **THEN** browser console shows an error message regardless of debug logging mode

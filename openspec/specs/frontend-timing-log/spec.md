## Purpose

Provide browser-side API timing logs so slow frontend requests can be identified during debugging.

## Requirements

### Requirement: Frontend SHALL log API request timing

The frontend API wrapper SHALL record and print request time to browser console.

#### Scenario: API call logged
- **WHEN** frontend calls `GET /api/session`
- **THEN** browser console shows `[API] GET /api/session 鈫?5ms`

#### Scenario: Slow request warning
- **WHEN** a request takes more than 1 second
- **THEN** console shows `[API][SLOW]` with the elapsed time

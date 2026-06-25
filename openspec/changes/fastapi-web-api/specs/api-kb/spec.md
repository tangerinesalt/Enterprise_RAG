## ADDED Requirements

### Requirement: API SHALL list all knowledge bases

The system SHALL return a list of all knowledge bases via REST API.

#### Scenario: GET /api/kb
- **WHEN** client sends `GET /api/kb`
- **THEN** response with 200 status and JSON array of KB names with file/folder counts

### Requirement: API SHALL create a knowledge base

The system SHALL create a new knowledge base via REST API.

#### Scenario: POST /api/kb
- **WHEN** client sends `POST /api/kb` with body `{"name": "my-docs"}`
- **THEN** a new KB is created
- **THEN** response returns `{"ok": true, "data": {"name": "my-docs"}}`

### Requirement: API SHALL show KB details

The system SHALL return a knowledge base's file list.

#### Scenario: GET /api/kb/{name}
- **WHEN** client sends `GET /api/kb/my-docs`
- **THEN** response includes file list with names and sizes

### Requirement: API SHALL delete a knowledge base

The system SHALL delete a knowledge base.

#### Scenario: DELETE /api/kb/{name}
- **WHEN** client sends `DELETE /api/kb/my-docs`
- **THEN** the KB directory is removed
- **THEN** response returns `{"ok": true}`

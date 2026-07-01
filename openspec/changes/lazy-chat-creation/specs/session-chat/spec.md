## ADDED Requirements

### Requirement: Frontend SHALL not auto-select chat on session page load

The frontend SHALL NOT automatically select or load any chat file when the user enters a session page. Chat files are loaded only on explicit user action (clicking a chat in the sidebar).

#### Scenario: No chat auto-selected on entry
- **WHEN** user navigates to `/session/<name>` via web UI
- **THEN** the session info and chat list are loaded from the server
- **THEN** no chat file content is fetched
- **THEN** no chat file is shown in the main content area

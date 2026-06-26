## ADDED Requirements

### Requirement: Navigation bar SHALL show current module

The top navigation bar SHALL display "知识库" and "会话" tabs, with the current module highlighted.

#### Scenario: Tab switches page
- **WHEN** user clicks "会话" tab
- **THEN** the page navigates to the session list
- **THEN** the "会话" tab is highlighted

#### Scenario: Page refresh preserves module
- **WHEN** user refreshes the browser on `/session/my-session`
- **THEN** the "会话" tab remains highlighted

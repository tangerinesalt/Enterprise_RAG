## Purpose

Define the top-level frontend navigation behavior between knowledge base and session modules.

## Requirements

### Requirement: Navigation bar SHALL show current module

The top navigation bar SHALL display "鐭ヨ瘑搴? and "浼氳瘽" tabs, with the current module highlighted.

#### Scenario: Tab switches page
- **WHEN** user clicks "浼氳瘽" tab
- **THEN** the page navigates to the session list
- **THEN** the "浼氳瘽" tab is highlighted

#### Scenario: Page refresh preserves module
- **WHEN** user refreshes the browser on `/session/my-session`
- **THEN** the "浼氳瘽" tab remains highlighted

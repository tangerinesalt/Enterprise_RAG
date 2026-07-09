## ADDED Requirements

### Requirement: Session chat history SHALL restore structured sources from persisted messages

The session chat page SHALL rebuild assistant source panels from persisted structured message fields when loading or reloading chat history.

#### Scenario: Reload history after streaming chat
- **WHEN** user completes a streaming chat, refreshes the page, and reopens that chat history
- **THEN** the assistant message is rendered from persisted message content
- **THEN** the source panel is restored from persisted structured sources

#### Scenario: Reload history after synchronous chat
- **WHEN** user opens a chat whose assistant response was created through the non-streaming chat API after this change
- **THEN** the page renders the assistant text
- **THEN** the page restores the same structured source panel shape as for streaming chats

### Requirement: Session chat page SHALL not depend on text parsing for source restoration

The session chat page SHALL treat structured persisted source fields as the authoritative source of citation data and SHALL NOT require reparsing assistant message text to rebuild source panels.

#### Scenario: Source restoration ignores markdown body parsing
- **WHEN** an assistant message body contains formatted markdown or citation-like text
- **THEN** the page still uses persisted structured source fields for the source panel
- **THEN** the source panel behavior is independent from markdown body formatting

#### Scenario: Legacy message without structured sources shows degraded history
- **WHEN** the page loads a legacy assistant message that has no persisted structured source fields
- **THEN** the page still renders the assistant body
- **THEN** the page does NOT attempt to rebuild a source panel by parsing the body text

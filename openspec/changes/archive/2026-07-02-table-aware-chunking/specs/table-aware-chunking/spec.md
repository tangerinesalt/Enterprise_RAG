## ADDED Requirements

### Requirement: Detect orphan table fragments

The system SHALL identify text nodes that contain Markdown pipe characters (`|`) but lack the table header separator line (`---|---|`), indicating a mid-table chunk split.

#### Scenario: Orphan detection on authority matrix page
- **WHEN** a page with a Markdown table is split into multiple nodes by SentenceSplitter
- **THEN** any node containing `|` but not containing `---` SHALL be flagged as an orphan fragment

#### Scenario: Non-table pipe content ignored
- **WHEN** a node contains `|` in non-table context (e.g., code, inline notes)
- **THEN** the system SHALL NOT flag it as an orphan unless it also has table-like row structure

### Requirement: Restore table headers to orphan fragments

The system SHALL prepend the nearest preceding column header row and separator line to each detected orphan fragment.

#### Scenario: Header inherited from previous node
- **WHEN** Node N contains the table header (`| 印章名称 | 审批人 |` + `|---|---|`) and Node N+1 is an orphan fragment
- **THEN** Node N+1's text SHALL be prepended with the header row and separator from Node N

#### Scenario: First node in document is orphan
- **WHEN** the very first node in a document is an orphan fragment (no preceding header exists)
- **THEN** the system SHALL leave it unchanged (no header to inherit)

#### Scenario: Multiple tables in sequence
- **WHEN** a node contains a new table header (`---`), the cached header SHALL be updated
- **THEN** subsequent orphans SHALL use the new header

### Requirement: Preserve existing node structure

The header restoration SHALL NOT merge nodes, change node count, or alter non-table content.

#### Scenario: Node count unchanged
- **WHEN** orphan fragments are fixed
- **THEN** the total number of nodes SHALL remain the same
- **THEN** only the `text` field of affected nodes SHALL be modified

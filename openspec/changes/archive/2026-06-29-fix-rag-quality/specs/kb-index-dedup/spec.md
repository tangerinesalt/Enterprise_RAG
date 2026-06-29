## ADDED Requirements

### Requirement: Index SHALL be idempotent per file

Calling `index_file` multiple times on the same file SHALL NOT create duplicate vectors in ChromaDB.

#### Scenario: Index same file twice
- **WHEN** user calls `index_file("my_kb", "doc.pdf")` twice
- **THEN** the first call indexes all chunks
- **THEN** the second call first deletes existing vectors for "doc.pdf" by `file_path` metadata
- **THEN** the second call then indexes fresh chunks
- **THEN** the total vector count equals the number of unique chunks, not a multiple

#### Scenario: Index all is idempotent
- **WHEN** user calls `index_all("my_kb")` twice
- **THEN** the total vector count after the second call does not increase (stays equal to unique chunks across all files)

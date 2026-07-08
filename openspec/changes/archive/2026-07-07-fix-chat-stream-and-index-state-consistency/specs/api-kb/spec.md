## MODIFIED Requirements

### Requirement: API SHALL show KB details

The system SHALL return a knowledge base's file list. For each file, the API SHALL expose the authoritative persisted indexing status for that specific file, including whether the file is indexed and the file-scoped chunk count when available.

#### Scenario: GET /api/kb/{name}
- **WHEN** client sends `GET /api/kb/my-docs`
- **THEN** response includes the file list with names and sizes
- **THEN** each file entry includes its persisted indexing status metadata when that metadata exists

## ADDED Requirements

### Requirement: API SHALL keep synchronous and streaming KB indexing status consistent

The system SHALL persist the same file-level indexing status semantics regardless of whether indexing is invoked through synchronous or streaming API paths.

#### Scenario: Synchronous indexing marks file as indexed
- **WHEN** client sends a synchronous indexing request for a file via `POST /api/kb/index` or `POST /api/kb/reindex`
- **THEN** the target file is persisted with `indexed` status on successful completion
- **THEN** the persisted `chunks` value reflects the number of chunks produced for that specific file

#### Scenario: Streaming indexing marks file as indexed
- **WHEN** client sends a streaming indexing request for a file via `POST /api/kb/index/stream`
- **THEN** the target file is persisted with `indexed` status on successful completion
- **THEN** the persisted `chunks` value reflects the number of chunks produced for that specific file

#### Scenario: Sync and stream paths report the same chunk semantics
- **WHEN** the same source file is indexed once through a synchronous path and once through a streaming path
- **THEN** both paths report chunk counts using the same file-scoped meaning
- **THEN** neither path reports the total vector count of the entire KB as if it were the file's chunk count

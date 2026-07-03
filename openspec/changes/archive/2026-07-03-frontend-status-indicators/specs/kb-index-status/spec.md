## ADDED Requirements

### Requirement: KB SHALL have an SSE streaming index endpoint

The system SHALL provide `POST /api/kb/index/stream` that returns a Server-Sent Events stream with per-chunk indexing progress. Each file being indexed SHALL emit `index_start`, multiple `index_progress`, and `index_done` events.

#### Scenario: Single file indexing emits progress events

- **WHEN** frontend calls `POST /api/kb/index/stream` with `{name: "my-docs", target: "report.pdf"}`
- **THEN** the SSE stream SHALL emit:
  1. `event: index_start\ndata: {"file": "report.pdf", "total_chunks": 50}\n\n`
  2. N × `event: index_progress\ndata: {"file": "report.pdf", "current": <1..50>, "total": 50, "pct": <2..100>}\n\n`
  3. `event: index_done\ndata: {"file": "report.pdf", "chunks": 50}\n\n`
- **AND** total_chunks SHALL equal the number of chunks produced by `chunk_documents()`
- **AND** `pct` SHALL be `Math.round(current / total * 100)`

#### Scenario: Index all emits events for each file

- **WHEN** frontend calls `POST /api/kb/index/stream` with `{name: "my-docs", all: true}`
- **THEN** the stream SHALL emit `index_start`/`index_progress`/`index_done` groups for each file, sequentially
- **AND** the stream SHALL end with `event: index_done\ndata: {"status": "all_complete", "files": <count>}\n\n`

### Requirement: KB SHALL persist file index final status

Each knowledge base SHALL maintain a `.index_status.json` file tracking the final indexing state of every file. The status file SHALL only persist terminal states (`pending` or `indexed`), not intermediate `indexing` state.

#### Scenario: Status file reflects completed indexes

- **WHEN** a file finishes indexing via `index_done` event
- **THEN** `.index_status.json` SHALL record the file as `"indexed"` with chunk count and timestamp

#### Scenario: Status file cleaned on file delete

- **WHEN** a file is deleted from the KB
- **THEN** its entry in `.index_status.json` SHALL be removed

### Requirement: KB detail API SHALL return file index status

`GET /api/kb/{name}` SHALL include an `indexed` field and `chunks` field for each file.

#### Scenario: API returns persisted status

- **WHEN** frontend calls `GET /api/kb/{name}`
- **THEN** each file object SHALL have `indexed` (`"pending"` or `"indexed"`) and `chunks` (number or null)
- **AND** the value SHALL be read from `.index_status.json` (not from ChromaDB)

### Requirement: Frontend SHALL show green fill progress bar per file

Each file row in the KB detail page SHALL display a horizontal progress bar below the filename. The bar SHALL fill with green color from left to right as chunks are embedded.

#### Scenario: Pending file shows empty bar

- **WHEN** a file has `indexed: "pending"`
- **THEN** the progress bar SHALL be empty (0% fill), styled with light gray background
- **AND** text SHALL show 「待索引」

#### Scenario: Indexing file shows growing green fill

- **WHEN** an `index_progress` event arrives for a file
- **THEN** the progress bar SHALL fill to `pct`% width with green color (`#22c55e`)
- **AND** the text SHALL update to show 「`pct`% 索引中 (`current`/`total` chunks)」
- **AND** the fill width SHALL animate with `transition: width 0.3s ease`

#### Scenario: Indexed file shows full green bar

- **WHEN** an `index_done` event arrives for a file
- **THEN** the progress bar SHALL be fully green (100%)
- **AND** the text SHALL show 「✓ 已索引 (`chunks` chunks)」

### Requirement: Frontend SHALL show index all summary progress

When "索引全部" is in progress, the button SHALL display an aggregate progress summary.

#### Scenario: Aggregate progress during batch indexing

- **WHEN** indexing multiple files
- **THEN** the "索引全部" button SHALL show 「`done_count`/`total_count` 文件」
- **AND** all file index buttons SHALL be disabled during the batch operation

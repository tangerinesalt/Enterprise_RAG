## ADDED Requirements

### Requirement: API SHALL maintain consistent file status semantics across sync and stream indexing

The KB indexing API SHALL ensure that synchronous indexing paths and streaming indexing paths persist the same per-file status contract. `indexed` SHALL mean a specific file has completed indexing successfully. `chunks` SHALL report the chunk count for that specific file, not a collection-wide total.

#### Scenario: Sync indexing persists status and returns node-level chunk count

- **WHEN** a client calls `POST /api/kb/index` (sync path)
- **THEN** the indexer computes chunk count from `len(nodes)` for the indexed file, not from `collection.count()`
- **THEN** the status file writes `set_file_status(..., "indexed", chunks=len(nodes))`
- **THEN** the API response includes file-level chunk count instead of collection-wide total

#### Scenario: Stream indexing uses node-level chunk count (not collection.count())

- **WHEN** a client calls `POST /api/kb/index/stream` (stream path)
- **THEN** each file's SSE `index_done` event carries `chunks=len(nodes)` for that file
- **THEN** the status file writes `set_file_status(..., "indexed", chunks=len(nodes))`
- **THEN** `collection.count()` is NOT used as the file's chunk count — it can include chunks from other files

#### Scenario: Reindex maintains the same file status contract

- **WHEN** a client calls `POST /api/kb/reindex`
- **THEN** each reindexed file computes file-level chunk counts
- **THEN** the status file's `indexed` and `chunks` use the same per-file semantics after reindex

### Requirement: API SHALL expose consistent per-file state in KB index responses

The file list data returned by `GET /api/kb/{name}` SHALL reflect the authoritative file state from the persisted status file, regardless of whether the most recent index used the sync or stream path.

#### Scenario: File list shows correct state after sync indexing

- **WHEN** a client indexes a file using the sync path
- **THEN** `GET /api/kb/{name}` returns that file's status as `indexed=true` with the actual file-level chunk count
- **THEN** the response is indistinguishable from the same request after stream indexing

#### Scenario: File status reflects error on index failure

- **WHEN** file processing fails during sync or stream indexing
- **THEN** `GET /api/kb/{name}` returns that file's status as `indexed=false` (or equivalent error state)
- **THEN** the error state is consistent across both paths

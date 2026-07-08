## MODIFIED Requirements

### Requirement: KB detail page SHALL show files and folders

The page SHALL display all files/folders in a KB and support upload, delete, and index. The page SHALL reflect authoritative indexing state per file and SHALL ensure progress indicators settle cleanly after both success and failure.

#### Scenario: View KB details
- **WHEN** user clicks a KB row
- **THEN** the page shows all files and folders in that KB

#### Scenario: Upload files
- **WHEN** user clicks upload button and selects files
- **THEN** files are uploaded via `POST /api/kb/upload`

#### Scenario: Index a file
- **WHEN** user clicks index button on a file row
- **THEN** the file is indexed via `POST /api/kb/index` or `POST /api/kb/index/stream`
- **THEN** the page shows indexing progress while the request is active
- **THEN** the page clears the in-progress state once the request reaches a terminal success state

#### Scenario: Index failure clears stuck progress
- **WHEN** a file indexing request fails through an SSE `index_error` event or request-level failure
- **THEN** the page removes the stale in-progress indicator for that file
- **THEN** the page can render the next authoritative file state from the backend without remaining stuck in "indexing"

#### Scenario: Bulk indexing failure clears bulk running state
- **WHEN** the user starts bulk indexing and one or more files fail or the stream request itself fails
- **THEN** the page clears the bulk indexing running state
- **THEN** the "index all" control does not remain permanently disabled because of stale local progress state

#### Scenario: Delete a file
- **WHEN** user clicks delete on a file/folder row
- **THEN** the file/folder is deleted

#### Scenario: Upload folder
- **WHEN** user clicks upload folder button
- **THEN** the folder is uploaded with directory structure preserved

## ADDED Requirements

### Requirement: KB detail page SHALL clean up stuck indexing progress on SSE errors and request failures

The KB detail page SHALL treat indexing progress as a state machine with explicit terminal cleanup. SSE `index_error` events, as well as request-level fetch failures, SHALL trigger cleanup of optimistic progress state so indicators do not remain stuck indefinitely.

#### Scenario: SSE index_error clears the affected file's progress

- **WHEN** streaming indexing sends an `index_error` SSE event for a file
- **THEN** that file's per-file progress UI is cleared
- **THEN** the file's index status reverts to its previous known value (or an error indicator)
- **THEN** other in-progress files continue unaffected

#### Scenario: Single-file error in bulk index stream does not permanently stall the UI

- **WHEN** a file's SSE `index_error` in a bulk streaming index causes its progress to leave the view
- **THEN** the bulk index progress bar does not permanently show as "in progress" due to a single file error
- **THEN** the user can still trigger index operations for other files

#### Scenario: Request-level failure cleans up optimistic progress

- **WHEN** a single-file `handleIndex()` or bulk `handleIndexAll()` call fails at the fetch level (network error, HTTP non-2xx) after optimistic progress was set
- **THEN** the page catches the error via try/catch or promise .catch()
- **THEN** the page clears any optimistic file progress state set for that request
- **THEN** for bulk indexing, the `isIndexingAll` flag is reset to `false`
- **THEN** the page is in a stable state where the user can retry

#### Scenario: handleIndexAll onError callback does not leave stale state

- **WHEN** bulk indexing's SSE `onError` callback fires for a file
- **THEN** the error handler clears the affected file's `indexingProgress` entry
- **THEN** `isIndexingAll` remains `true` if other files are still processing
- **THEN** the `onAllDone` or terminal callback eventually resets `isIndexingAll` to `false`
- **THEN** if no `onAllDone` fires, the page does not leave `isIndexingAll` stuck at `true`

#### Scenario: Successful completion clears progress and shows final state

- **WHEN** indexing completes successfully (sync or stream)
- **THEN** per-file progress is cleared
- **THEN** the files' latest `indexed`/`chunks` state is reflected in the file list
- **THEN** for bulk index runs, `isIndexingAll` is reset
- **THEN** the page does not show stale "in progress" indicators

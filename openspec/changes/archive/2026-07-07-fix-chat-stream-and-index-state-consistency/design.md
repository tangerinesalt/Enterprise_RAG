## Context

This change spans both the session chat flow and the KB indexing flow. The chat issue is a frontend lifecycle problem: `SessionChat` owns a local `AbortController`, but stream cancellation is only triggered before a new send or on unmount, not when the local chat target changes. The KB issues cross frontend and backend boundaries: `KbDetail` tracks optimistic in-memory indexing progress, while `Indexer` and the KB APIs define the persisted source of truth for file indexing status.

The current indexing implementation also exposes two different semantics depending on the path used. Streaming indexing updates `.index_status.json` and returns chunk progress, while synchronous indexing returns collection-wide counts and does not fully maintain the same per-file persisted status contract. The result is a mismatch between what the UI presents and what the backend actually guarantees.

## Goals / Non-Goals

**Goals:**
- Ensure obsolete streamed chat responses cannot continue mutating the active local chat view after a chat switch or deletion.
- Ensure KB indexing progress state always reaches a terminal UI state on success and failure.
- Align synchronous KB indexing with streaming indexing so persisted file status and reported chunk counts mean the same thing across all entry points.
- Add regression coverage around the above behaviors.

**Non-Goals:**
- Do not redesign the overall session chat architecture or replace SSE with another transport.
- Do not change retrieval quality, reranking strategy, or LLM behavior.
- Do not migrate KB or session persistence away from the current local filesystem model.
- Do not address unrelated repo concerns such as bundle size, CORS policy, or model path portability in this change.

## Decisions

### Decision 1: Treat local chat-view changes as stream termination points

Any action that invalidates the current local chat target must terminate the in-flight stream before mutating selection state. Concretely, switching chats and deleting the currently selected chat will use the same abort path already used before starting a new stream.

This keeps the contract simple:
- one local page has at most one active stream
- a stream is only allowed to update the chat view it was started for
- once the page target changes, the old stream is considered stale and must stop

Alternative considered:
- Leave the stream alive and ignore late tokens in callbacks by checking chat IDs.
  Rejected because it spreads stale-stream guards across multiple callbacks and still keeps an unnecessary network request alive.

### Decision 2: Make KB progress cleanup explicit in both SSE-event and request-failure paths

The KB detail page will treat indexing progress as a state machine with explicit terminal cleanup:
- success clears per-file progress and, for bulk runs, clears the global indexing state
- `index_error` clears the affected file’s progress
- request-level failure or thrown fetch errors clear any optimistic progress introduced before the stream began

This is intentionally handled in the page layer instead of only in the API helper, because the page owns both per-file progress state and the bulk-run `isIndexingAll` flag.

Alternative considered:
- Hide cleanup inside `kbApi.indexStream()` only.
  Rejected because the API helper cannot safely reason about page-specific optimistic state keys or bulk-page UX flags.

### Decision 3: Define per-file indexing status as the authoritative contract

The authoritative indexing contract will be:
- `indexed` means the specific file has completed indexing successfully
- `chunks` means the number of chunks produced for that specific file
- sync and stream indexing paths must persist and report the same semantics

To get there, synchronous indexing must stop returning collection-wide `collection.count()` values as if they were file-level counts. Instead, indexing should compute and persist the file-scoped chunk count directly from the produced nodes, and write `set_file_status(..., "indexed", chunks=<file_chunks>)` in both sync and stream paths.

Alternative considered:
- Keep collection-wide counts and document them as “current KB size”.
  Rejected because the UI and status file are file-oriented, not KB-total-oriented, and the current naming already implies file-local semantics.

### Decision 4: Regressions should be tested at the behavior boundary, not only helper level

Tests will focus on externally meaningful guarantees:
- stale chat streams cannot keep mutating the page after the selected chat changes
- KB progress state does not remain stuck after failure
- sync and stream indexing produce the same persisted file-status meaning

This may require a combination of unit tests for backend indexing semantics and targeted frontend/component tests or lightweight logic extraction for UI state transitions.

Alternative considered:
- Limit tests to backend-only coverage because frontend already builds.
  Rejected because two of the three confirmed issues are UI lifecycle/state problems, and a successful build does not validate those behaviors.

## Risks / Trade-offs

- [Risk] Adding more explicit abort behavior could expose latent assumptions in the chat page about when `loading` resets.
  Mitigation: keep abort handling centralized and test chat switch, delete-current-chat, and send-new-message paths together.

- [Risk] Refactoring sync indexing to use file-scoped counts may require touching multiple call sites that currently assume returned counts are collection totals.
  Mitigation: update API responses, persisted status writes, and any CLI-facing messages in one pass, then verify consistency through regression tests.

- [Risk] KB progress cleanup code can become duplicated between single-file and bulk indexing flows.
  Mitigation: factor shared cleanup helpers inside the page component if needed, while keeping ownership of page-local state in the UI layer.

## Migration Plan

1. Lock in expected behavior with regression tests for the three confirmed issues.
2. Update `SessionChat` stream lifecycle handling so chat switch and current-chat deletion abort obsolete streams.
3. Fix KB page cleanup paths for SSE errors and request failures.
4. Refactor synchronous indexing to persist file-scoped `indexed/chunks` semantics consistently with streaming indexing.
5. Run backend tests and frontend build, and add any frontend-level verification required by the new regression coverage.

## Open Questions

- Whether frontend regression coverage should be added as component tests in the existing stack or via extracted pure state helpers depends on what test tooling already exists locally. The behavioral requirement is fixed either way.

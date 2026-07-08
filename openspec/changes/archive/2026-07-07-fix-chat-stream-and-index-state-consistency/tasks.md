## 1. Chat Stream Lifecycle Safety

- [ ] 1.1 Add regression coverage for switching chats and deleting the current chat while a stream is active.
- [ ] 1.2 Update `ui/src/pages/SessionChat.tsx` so chat switches cancel obsolete in-flight streams before local selection changes.
- [ ] 1.3 Update current-chat deletion flow so deleting the selected chat cancels the obsolete stream before the replacement view is chosen.

## 2. KB Progress State Recovery

- [ ] 2.1 Add regression coverage for KB indexing failure-state recovery and non-stuck progress indicators.
- [ ] 2.2 Update `ui/src/pages/KbDetail.tsx` to clear per-file progress state on SSE `index_error` events.
- [ ] 2.3 Update single-file and bulk indexing flows to clear optimistic progress and `isIndexingAll` on request-level failures.

## 3. Sync and Stream Index Status Consistency

- [ ] 3.1 Add backend regression coverage proving sync and stream indexing persist the same file-level `indexed/chunks` semantics.
- [ ] 3.2 Refactor `app/modules/kb_manager/indexer.py` so synchronous indexing computes and returns file-scoped chunk counts instead of collection-wide totals.
- [ ] 3.3 Persist `set_file_status(..., "indexed", chunks=<file_chunks>)` consistently across synchronous and streaming indexing paths, and verify related API responses remain aligned.

## 4. Verification

- [ ] 4.1 Run backend automated tests covering chat lifecycle and KB indexing consistency.
- [ ] 4.2 Run frontend build and any added frontend-level verification for stream cancellation and KB progress recovery.
- [ ] 4.3 Re-check the change artifacts for consistency and confirm the change is ready for `/opsx:apply`.

## Why

The current project has three user-visible consistency gaps: streamed chat output can continue writing into the wrong chat view after the user switches context, KB indexing progress can get stuck in the UI after failure, and synchronous KB indexing does not maintain the same persisted file status semantics as streaming indexing. These issues break trust in the UI state and make it hard to tell which chat or file state is authoritative.

## What Changes

- Ensure the session chat page cancels any in-flight streaming response before switching chats or deleting the currently selected chat, so streamed tokens cannot leak into the wrong local chat view.
- Harden KB indexing progress handling in the frontend so file-level and bulk indexing indicators always settle cleanly on success, SSE error events, and request-level failures.
- Make synchronous KB indexing paths persist the same file status contract as streaming indexing paths, including correct `indexed` state updates and file-scoped chunk accounting instead of collection-wide counts.
- Add regression coverage for chat-stream cancellation behavior, KB indexing failure-state cleanup, and sync-vs-stream index status consistency.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `session-chat`: clarify that streamed chat output must remain scoped to the locally selected target chat and must stop updating the UI once that chat is no longer the active local view.
- `ui-session-page`: strengthen local chat-view state handling so chat switches and current-chat deletion cancel obsolete streams instead of letting stale output mutate the current page state.
- `api-kb`: tighten KB indexing response semantics so synchronous indexing and reindexing keep persisted file status metadata consistent with streaming indexing.
- `ui-kb-page`: require indexing progress indicators to recover cleanly from failures and reflect the final authoritative file state.
- `auto-test`: add regression requirements covering stream cancellation and KB index-state consistency across success and failure paths.

## Impact

- Frontend session flow: `ui/src/pages/SessionChat.tsx`, related chat-state wiring, and stream lifecycle handling in `ui/src/api/index.ts`
- Frontend KB flow: `ui/src/pages/KbDetail.tsx` and related SSE progress handling
- Backend KB indexing: `app/modules/kb_manager/indexer.py`, `app/api/routers/kb.py`, and persisted file-status helpers in `app/modules/kb_manager/knowledge_base.py`
- Tests: additions in `tests/unit`, and possibly integration coverage for API-visible indexing semantics

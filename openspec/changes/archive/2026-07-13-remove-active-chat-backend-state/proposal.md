## Why

`active_chat` no longer participates in authoritative chat targeting, but it still exists as persisted backend state, public API response data, a dedicated route, and a set of concurrency tests. That leftover contract creates misleading shared-session semantics for LAN multi-user usage and keeps unnecessary coupling between backend metadata and frontend local selection.

## What Changes

- Remove persisted `active_chat` from session config and stop reading or writing it anywhere in backend session flows.
- **BREAKING** Remove the backend chat-selection contract: delete the session select API path and stop returning `active_chat` / `is_active` from session APIs.
- Remove backend and CLI code paths that exist only to maintain active-chat metadata.
- Update frontend session page integration to rely exclusively on local `chat_file` state and stop calling the removed selection API.
- Replace metadata-oriented regression tests with tests that verify explicit `chat_file` routing, response-shape changes, migration safety for legacy config files, and unaffected same-session concurrency.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `api-session`: Remove active-chat metadata and the selection endpoint from the public session API contract.
- `session-management`: Remove persisted recent-selection state from session metadata and user-visible session inspection flows.
- `session-chat-concurrency`: Reframe same-session concurrency guarantees around explicit `chat_file` isolation without any session-global selected-chat metadata.
- `session-storage-safety`: Remove active-chat-specific persistence assumptions while preserving atomic config and chat-file safety.
- `ui-session-page`: Make chat switching a purely local UI concern with no backend selection writeback.
- `auto-test`: Update regression expectations so automated tests cover the fully removed contract and preserve concurrency guarantees.

## Impact

- Affected backend files include `app/modules/session/session_manager.py`, `app/api/routers/session.py`, `app/api/schemas.py`, and `app/modules/session/cli.py`.
- Affected frontend files include `ui/src/api/index.ts` and `ui/src/pages/SessionChat.tsx`, plus any type consumers of `active_chat` or `is_active`.
- Affected tests include session API tests, same-session concurrency tests, session write-safety tests, and frontend integration expectations that still assume `/api/session/select` exists.
- This is a breaking API and CLI cleanup for consumers that still rely on `active_chat`, `/api/session/select`, or `is_active`.

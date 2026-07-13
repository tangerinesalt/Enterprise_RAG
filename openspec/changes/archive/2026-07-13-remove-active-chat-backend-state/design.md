## Context

The current session model already treats explicit `chat_file` as the authoritative target for synchronous and streaming chat requests. `active_chat` survives only as shared backend metadata: it is persisted in `config.json`, exposed through session APIs, maintained by a dedicated selection route and CLI command, and asserted by concurrency tests. In a LAN multi-user setting, that metadata implies a false session-global "current chat" and introduces avoidable shared-state churn.

This change removes the contract completely rather than deprecating it. That means the backend, frontend client, CLI, and regression tests all need to stop referencing `active_chat` and `is_active`.

## Goals / Non-Goals

**Goals:**

- Make `chat_file` the only backend-recognized chat target identifier.
- Remove session-global selected-chat persistence, API fields, and selection endpoints.
- Keep legacy `config.json` readable during migration while ensuring rewritten config files no longer contain `active_chat`.
- Preserve existing same-session concurrency guarantees for explicit `chat_file` requests.
- Replace metadata-based tests with contract tests that verify the removed fields and unaffected chat routing behavior.

**Non-Goals:**

- Redesign the frontend route model or introduce URL-based chat selection persistence.
- Change chat preview behavior or the first-submit chat creation model.
- Change chat-file locking, streaming semantics, or KB retrieval behavior beyond removing metadata-specific paths.

## Decisions

### 1. Remove `active_chat` as a hard contract instead of keeping a null-valued compatibility field

The backend will stop exposing `active_chat` in session detail/list responses and stop exposing `is_active` in chat lists. Keeping the fields as permanently-null compatibility placeholders would preserve ambiguity, prolong client coupling, and weaken test clarity.

Alternative considered:
- Soft-delete with `active_chat: null` and a no-op `/session/select` endpoint.
- Rejected because it keeps dead API surface and encourages clients to keep sending useless selection writes.

### 2. Delete the selection write path end-to-end

`SessionSelectChatRequest`, `SessionManager.select_chat()`, the `/api/session/select` route, and the CLI `session select` command will be removed. Frontend chat switching will remain local state only.

Alternative considered:
- Keep backend selection writes for CLI only.
- Rejected because it preserves the same shared-state model under a different entry point and complicates tests and docs.

### 3. Treat legacy config files as readable input but not preserved output

The config loader will tolerate older `config.json` files that still contain `active_chat`. Any subsequent config write will omit the field, so migration happens opportunistically without a one-time data rewrite job.

Alternative considered:
- Add a startup migration that rewrites every session config.
- Rejected because it adds operational complexity and failure modes without real benefit for a small local-storage app.

### 4. Replace metadata-oriented tests with explicit contract tests

Tests will stop asserting that concurrent operations preserve or update `active_chat`. They will instead assert:

- session APIs do not return `active_chat`
- chat list entries do not return `is_active`
- removed API/CLI paths fail or disappear as expected
- explicit `chat_file` requests remain stable under concurrent unrelated config updates
- legacy configs with `active_chat` still load and can be rewritten without the field

Alternative considered:
- Only delete obsolete tests.
- Rejected because full removal is a contract change; absence of replacement tests would reduce confidence in API shape, migration safety, and concurrency regressions.

## Risks / Trade-offs

- [Breaking API clients] Existing callers of `/api/session/select`, `active_chat`, or `is_active` will fail after removal. → Mitigation: update frontend in the same change and document the removal in proposal/spec/tasks.
- [Legacy session config ambiguity] Older configs may still contain `active_chat` until another write occurs. → Mitigation: loader ignores the field semantically, and rewrite-path tests verify it disappears on next persisted update.
- [Test gap during refactor] Removing metadata assertions could accidentally reduce concurrency coverage. → Mitigation: add replacement tests for explicit `chat_file` stability, response shape, and legacy-config migration.
- [CLI behavior change] Operators used to `session select` will lose that command. → Mitigation: keep CLI session list/info focused on real persisted data and remove active markers from output expectations.

## Migration Plan

1. Remove `active_chat` and `is_active` from backend response builders and persistence defaults.
2. Delete backend request schema, route, manager method, and CLI command that exist only for chat selection metadata.
3. Update frontend client types and page logic to stop calling `/api/session/select` and stop expecting returned active markers.
4. Add migration-safe loader behavior and tests for legacy configs containing `active_chat`.
5. Update regression suites and contract tests before final verification.

Rollback:

- Restore the removed route, response fields, and config writes in one revert if downstream clients are still coupled.
- No persisted data migration is destructive, so rollback only requires code restoration.

## Open Questions

- Whether the frontend should later persist local chat selection in URL or `localStorage` is intentionally deferred.
- Whether the CLI should gain a replacement convenience command for "open most recent chat" is out of scope for this removal.

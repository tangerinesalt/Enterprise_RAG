## 1. Backend contract removal

- [x] 1.1 Remove `active_chat` from session config defaults, loaders, writers, and delete-path cleanup in `SessionManager`.
- [x] 1.2 Remove `SessionManager.select_chat()`, `SessionSelectChatRequest`, and the `/api/session/select` route.
- [x] 1.3 Remove `active_chat` and `is_active` from session/list/chat-list response builders and any related CLI output.

## 2. Frontend and client alignment

- [x] 2.1 Remove `active_chat` / `is_active` from frontend API types and any code that expects them.
- [x] 2.2 Update the session chat page to stop calling `/api/session/select` and rely only on local `activeChat` state plus explicit `chat_file`.
- [x] 2.3 Verify chat switching, new-chat creation, and reload flows still work without backend selection metadata.

## 3. Migration-safe regression coverage

- [x] 3.1 Replace metadata-oriented unit tests with tests that verify explicit `chat_file` stability under unrelated config writes.
- [x] 3.2 Add tests asserting session APIs no longer expose `active_chat` or `is_active`, and that `POST /api/session/select` is unsupported.
- [x] 3.3 Add tests seeding a legacy `config.json` with `active_chat` and verifying the session still loads and rewrites without that field.
- [x] 3.4 Update any CLI or session-info tests to reflect the removed active-chat output and command surface.

## 4. Verification

- [x] 4.1 Run targeted backend unit tests covering session management, session concurrency, and storage safety.
- [x] 4.2 Run frontend lint/build or relevant UI tests to confirm the client no longer references removed API fields.
- [x] 4.3 Perform a focused manual verification of multi-chat switching and same-session concurrent usage behavior after the contract removal.

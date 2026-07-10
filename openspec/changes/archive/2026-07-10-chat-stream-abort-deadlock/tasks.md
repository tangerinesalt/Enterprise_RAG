## 1. Lock Scope Restructure (Root Cause Fix)

- [x] 1.1 Restructured `chat_stream()` into 3 phases: prepare (lock) → retrieve/generate (no lock) → persist (lock)
- [x] 1.2 Added `except GeneratorExit` before `except Exception` — catches client disconnect cleanly during phase 2
- [x] 1.3 All tests pass: 63/63

## 2. Rollback Logic — Removed

- [x] 2.1 Verified `SimpleChatStore` API (`delete_last_message(key)` available)
- [x] 2.2 Implemented `_rollback_last_user_message()` but **reverted**: user message after cancellation is legitimate data (confirmed by existing unit tests)
- [x] 2.3 Removed rollback from GeneratorExit handler — only `raise` to terminate cleanly

## 3. Router-level Disconnect Detection

- [x] 3.1 Added `request: Request` param + `request.is_disconnected` check before each yield in `generate()`
- [x] 3.2 Added `try/except GeneratorExit` in `generate()` for clean exit

## 4. Auto-repair Orphaned Messages — Not Needed

- [x] 4.1 Investigated: existing cancellation tests confirm user message retention is expected behavior
- [x] 4.2 Removed auto-repair logic; no orphan repair needed

## 5. Verify

- [ ] 5.1 Manual test: start stream, switch chat mid-stream, verify Chat A works again
- [ ] 5.2 Manual test: complete a conversation in a previously-aborted chat, switch away and back, verify no hang
- [x] 5.3 Run existing unit tests (persistence): 3/3 passed
- [x] 5.4 Run all unit tests: 63/63 passed ✅

## 1. Diagnosis

- [ ] 1.1 Add `request_id` (uuid4) to each `chat_stream()` invocation
- [ ] 1.2 Log `request_id` at phase transitions: `phase=1-prepare`, `phase=2-retrieval`, `phase=2-generation llm_started`, `phase=3-persist`
- [ ] 1.3 Log `request_id` before and after `query_engine.query(query)` and inside `for chunk in response.response_gen`
- [ ] 1.4 Deploy and reproduce: open two tabs, send messages simultaneously, capture logs

## 2. Fix (contingent on diagnosis)

- [ ] 2.1 If httpx client shared: create per-request LLM client in `chat_stream` phase 2
- [ ] 2.2 If response_gen routing issue: verify standalone httpx client resolves it
- [ ] 2.3 If session config racing: isolate `_ensure_chat_target`'s `_save_config` from the active stream path

## 3. Verify

- [ ] 3.1 Run `pytest tests/unit/`
- [ ] 3.2 Manual: two tabs, concurrent messages, both respond correctly
- [ ] 3.3 Manual: rapid switch between tabs during streaming, no response loss

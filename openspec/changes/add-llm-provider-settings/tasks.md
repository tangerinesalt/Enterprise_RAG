## 1. Configuration

- [ ] 1.1 Add `LLM_PROVIDER`, `LLM_URL`, `LLM_MODEL`, and `LLM_TOKEN` exports in `config/settings.py`.
- [ ] 1.2 Normalize `LLM_PROVIDER` to lowercase and default it to `ollama` when omitted.
- [ ] 1.3 Preserve compatibility aliases from `ES_URL`, `ES_MODEL`, and `ES_TOKEN` when canonical `LLM_*` values are absent.
- [ ] 1.4 Define provider-specific defaults for Ollama, DeepSeek, and OpenAI where appropriate.

## 2. LLM Initialization

- [ ] 2.1 Update `config/llm.py` to select the LlamaIndex LLM class based on `LLM_PROVIDER`.
- [ ] 2.2 Keep `ollama` routed through `llama_index.llms.ollama.Ollama`.
- [ ] 2.3 Route `deepseek` through `llama_index.llms.openai.OpenAI` with the configured API base URL, model, and token.
- [ ] 2.4 Route `openai` through `llama_index.llms.openai.OpenAI` with the configured API base URL, model, and token.
- [ ] 2.5 Raise clear configuration errors for unsupported providers and missing hosted-provider tokens.

## 3. Documentation And Examples

- [ ] 3.1 Update `settings.json` or `.env.example` examples to show `LLM_PROVIDER`.
- [ ] 3.2 Document Ollama, DeepSeek, and OpenAI configuration examples in the project README.
- [ ] 3.3 Note that embedding configuration remains unchanged.

## 4. Verification

- [ ] 4.1 Add or update tests for default Ollama provider behavior.
- [ ] 4.2 Add or update tests for canonical `LLM_*` keys and legacy `ES_*` alias behavior.
- [ ] 4.3 Add or update tests for DeepSeek and OpenAI provider construction without making network calls.
- [ ] 4.4 Add or update tests for invalid provider and missing token errors.
- [ ] 4.5 Run the relevant test suite and a smoke import of `config.init.init_models()`.

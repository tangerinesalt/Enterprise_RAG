## Context

Runtime model setup is centralized under `config/`. `config/settings.py` reads the root `settings.json`, `config/llm.py` initializes `llama_index.core.Settings.llm`, and consumers rely on the configured global `Settings` instance.

The current LLM initialization always imports and constructs `llama_index.llms.ollama.Ollama` using `OLLAMA_URL` and `LLM_MODEL`. That works for local Ollama but makes DeepSeek and OpenAI require code edits. The existing `settings.json` uses `ES_URL`, `ES_MODEL`, and `ES_TOKEN`; those names should remain usable during migration.

## Goals / Non-Goals

**Goals:**

- Add an explicit `LLM_PROVIDER` setting with supported values `ollama`, `deepseek`, and `openai`.
- Route `LLM_PROVIDER=ollama` through `llama_index.llms.ollama.Ollama`.
- Route `LLM_PROVIDER=deepseek` and `LLM_PROVIDER=openai` through `llama_index.llms.openai.OpenAI`, using provider-specific base URL and API key settings.
- Preserve the existing Ollama default when no provider is configured.
- Keep all model consumers unchanged; only central configuration code should know about providers.

**Non-Goals:**

- Changing embedding provider selection.
- Adding a UI for editing provider settings.
- Supporting arbitrary provider plugins beyond the three named providers.
- Changing session, retrieval, or prompt behavior.

## Decisions

### Use a single provider switch in `config.llm`

`init_llm()` should branch on a normalized provider value from `config.settings`. This keeps provider-specific imports and constructor arguments in one place.

Alternative considered: create separate modules like `config/llms/openai.py` and `config/llms/ollama.py`. That is more extensible, but the current scope only has three providers and one initialization function, so a small internal factory is simpler and easier to test.

### Keep Ollama backward compatible

When `LLM_PROVIDER` is absent, empty, or set to `ollama`, `Settings.llm` should continue to be an `Ollama` instance using the existing local defaults. `ES_URL` and `ES_MODEL` should remain supported aliases for `LLM_URL` and `LLM_MODEL`.

Alternative considered: require all users to rename keys immediately. That would make configuration clearer but would break the current `settings.json` without functional benefit.

### Treat DeepSeek as OpenAI-compatible

DeepSeek should use `llama_index.llms.openai.OpenAI` with a DeepSeek API base URL and API token. This avoids a separate DeepSeek-specific dependency and matches the common OpenAI-compatible API pattern.

Alternative considered: add a dedicated DeepSeek client package. That increases dependency surface and is unnecessary unless DeepSeek-specific features are required later.

### Use canonical setting names with legacy aliases

Preferred names:

- `LLM_PROVIDER`
- `LLM_URL`
- `LLM_MODEL`
- `LLM_TOKEN`

Legacy aliases:

- `ES_URL` for `LLM_URL`
- `ES_MODEL` for `LLM_MODEL`
- `ES_TOKEN` for `LLM_TOKEN`

Provider-specific defaults should be applied only when the matching provider does not specify a value. For example, OpenAI and DeepSeek require a token, while Ollama can keep using a local unauthenticated endpoint.

## Risks / Trade-offs

- Invalid provider value -> fail fast with a clear configuration error listing supported providers.
- Missing hosted-provider token -> fail fast before the first chat request, so runtime failures are easier to diagnose.
- DeepSeek OpenAI-compatible behavior may diverge from OpenAI for some advanced features -> keep the first implementation limited to normal chat completion parameters.
- Legacy `ES_*` naming is confusing -> document canonical `LLM_*` names and keep aliases only for compatibility.

## Migration Plan

1. Add `LLM_PROVIDER` parsing with default `ollama`.
2. Add canonical `LLM_*` settings while preserving `ES_*` fallbacks.
3. Update `config.llm.init_llm()` provider selection.
4. Update example configuration and README snippets to show the new provider field.
5. Add focused tests for Ollama default behavior, OpenAI construction, DeepSeek construction, invalid provider errors, and missing token errors.

Rollback is straightforward: set `LLM_PROVIDER` to `ollama` or remove it, and the system should behave like the current local Ollama setup.

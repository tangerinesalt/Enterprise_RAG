## Why

The project currently initializes `Settings.llm` as an Ollama model unconditionally, so switching the chat LLM to hosted providers requires code changes instead of configuration changes. Adding an explicit provider option to `settings.json` makes model selection visible, repeatable, and easier to extend while preserving Ollama as the local default.

## What Changes

- Add an LLM provider setting with supported values `ollama`, `deepseek`, and `openai`.
- Update the central LLM initialization contract so `config.llm.init_llm()` selects the appropriate LlamaIndex LLM integration based on the configured provider.
- Preserve current Ollama behavior when the provider is omitted or set to `ollama`.
- Define provider-specific URL, model, and token handling for hosted providers without requiring consumer code changes.
- Keep embedding configuration unchanged for this change.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `model-config`: LLM configuration changes from Ollama-only initialization to provider-based initialization for Ollama, DeepSeek, and OpenAI.

## Impact

- Affected configuration: `settings.json`, `.env.example` or configuration documentation if present.
- Affected backend code: `config/settings.py`, `config/llm.py`, and any tests covering model initialization.
- Affected dependencies: may require LlamaIndex provider packages for OpenAI-compatible hosted LLMs if they are not already installed.
- Consumer modules should continue using preconfigured `llama_index.core.Settings` and should not instantiate provider clients directly.

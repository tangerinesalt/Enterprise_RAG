## ADDED Requirements

### Requirement: System SHALL expose an LLM provider setting

The system SHALL read an LLM provider setting from runtime configuration and SHALL support the provider values `ollama`, `deepseek`, and `openai`.

#### Scenario: Provider defaults to Ollama
- **WHEN** `settings.json` does not define an LLM provider
- **THEN** `config.settings` exposes the LLM provider as `ollama`

#### Scenario: Provider is normalized
- **WHEN** `settings.json` defines the LLM provider with surrounding whitespace or uppercase letters
- **THEN** `config.settings` exposes the normalized lowercase provider value

#### Scenario: Unsupported provider is rejected
- **WHEN** `config.llm.init_llm()` is called with an unsupported LLM provider
- **THEN** initialization fails with an error that identifies the unsupported provider
- **THEN** the error lists `ollama`, `deepseek`, and `openai` as supported values

### Requirement: System SHALL support canonical LLM configuration keys

The system SHALL support canonical LLM configuration keys for provider, base URL, model, and token while preserving existing `ES_*` keys as compatibility aliases.

#### Scenario: Canonical keys are used
- **WHEN** `settings.json` defines `LLM_URL`, `LLM_MODEL`, and `LLM_TOKEN`
- **THEN** `config.settings` exposes those values for LLM initialization

#### Scenario: Legacy keys remain supported
- **WHEN** `settings.json` omits canonical LLM URL, model, or token keys but defines `ES_URL`, `ES_MODEL`, or `ES_TOKEN`
- **THEN** `config.settings` uses the matching `ES_*` value as the LLM setting

## MODIFIED Requirements

### Requirement: System SHALL configure LLM centrally

The system SHALL provide a single function `init_llm()` in `config/llm.py` that initializes the global LLM based on the configured LLM provider.

#### Scenario: Ollama LLM is set on Settings
- **WHEN** `config.llm.init_llm()` is called with LLM provider `ollama`
- **THEN** `Settings.llm` is set to a configured `llama_index.llms.ollama.Ollama` instance
- **THEN** the instance uses the configured LLM URL and model from `config.settings`

#### Scenario: DeepSeek LLM is set on Settings
- **WHEN** `config.llm.init_llm()` is called with LLM provider `deepseek`
- **THEN** `Settings.llm` is set to a configured `llama_index.llms.openai.OpenAI` instance
- **THEN** the instance uses the configured DeepSeek-compatible API base URL, model, and token from `config.settings`

#### Scenario: OpenAI LLM is set on Settings
- **WHEN** `config.llm.init_llm()` is called with LLM provider `openai`
- **THEN** `Settings.llm` is set to a configured `llama_index.llms.openai.OpenAI` instance
- **THEN** the instance uses the configured OpenAI API base URL, model, and token from `config.settings`

#### Scenario: Hosted provider token is required
- **WHEN** `config.llm.init_llm()` is called with LLM provider `deepseek` or `openai`
- **THEN** initialization requires a non-empty LLM token
- **THEN** initialization fails with a clear configuration error if the token is missing

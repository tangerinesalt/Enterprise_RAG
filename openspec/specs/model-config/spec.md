## ADDED Requirements

### Requirement: System SHALL configure Embedding model centrally

The system SHALL provide a single function `init_embedding()` in `config/embedding.py` that initializes the global embedding model.

#### Scenario: Embedding model is set on Settings
- **WHEN** `config.embedding.init_embedding()` is called
- **THEN** `Settings.embed_model` is set to a configured `OllamaEmbedding` instance
- **THEN** the instance uses `EMBED_URL` and `EMBED_MODEL` from `config.settings`

#### Scenario: Changing embedding model
- **WHEN** `EMBED_URL` or `EMBED_MODEL` in `config.settings` is changed
- **THEN** calling `init_embedding()` uses the new values
- **THEN** no consumer code needs modification

### Requirement: System SHALL configure LLM centrally

The system SHALL provide a single function `init_llm()` in `config/llm.py` that initializes the global LLM.

#### Scenario: LLM is set on Settings
- **WHEN** `config.llm.init_llm()` is called
- **THEN** `Settings.llm` is set to a configured `Ollama` instance
- **THEN** the instance uses `OLLAMA_URL` and `LLM_MODEL` from `config.settings`

### Requirement: System SHALL provide a unified initialization entry point

The system SHALL provide `config.init.init_models()` that calls both `init_embedding()` and `init_llm()`.

#### Scenario: Both models initialized
- **WHEN** `config.init.init_models()` is called
- **THEN** `init_embedding()` is called
- **THEN** `init_llm()` is called
- **THEN** both `Settings.embed_model` and `Settings.llm` are configured

### Requirement: Consumers SHALL NOT instantiate models directly

All consumer code (indexer, test scripts, API routes) SHALL rely on `Settings` being pre-configured, rather than creating model instances.

#### Scenario: Indexer uses Settings
- **WHEN** `init_models()` has been called and indexer runs
- **THEN** `Settings.embed_model` is already set
- **THEN** indexer does NOT import `OllamaEmbedding`
- **THEN** indexer does NOT set `Settings.embed_model`

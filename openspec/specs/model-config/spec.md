## ADDED Requirements

### Requirement: 系统 SHALL 暴露 LLM provider 设置

系统 SHALL 从运行时配置中读取 LLM provider，并 SHALL 支持 `ollama`、`deepseek` 和 `openai` 三个 provider 值。

#### Scenario: provider 默认使用 Ollama
- **WHEN** `settings.json` 未定义 LLM provider
- **THEN** `config.settings` 暴露的 LLM provider SHALL 为 `ollama`

#### Scenario: provider 会被标准化
- **WHEN** `settings.json` 中的 LLM provider 包含前后空格或大写字母
- **THEN** `config.settings` 暴露的 provider 值 SHALL 为标准化后的 lowercase 值

#### Scenario: 不支持的 provider 会被拒绝
- **WHEN** 使用不支持的 LLM provider 调用 `config.llm.init_llm()`
- **THEN** 初始化 SHALL 失败，并在错误中指出不支持的 provider
- **THEN** 错误 SHALL 列出 `ollama`、`deepseek` 和 `openai` 作为支持值

### Requirement: 系统 SHALL 支持标准 LLM 配置键

系统 SHALL 支持用于 provider、base URL、模型名和 token 的标准 LLM 配置键，并 SHALL 保留现有 `ES_*` 配置键作为兼容别名。

#### Scenario: 使用标准配置键
- **WHEN** `settings.json` 定义 `LLM_URL`、`LLM_MODEL` 和 `LLM_TOKEN`
- **THEN** `config.settings` SHALL 暴露这些值用于 LLM 初始化

#### Scenario: 旧配置键仍然可用
- **WHEN** `settings.json` 未定义标准 LLM URL、模型名或 token，但定义了 `ES_URL`、`ES_MODEL` 或 `ES_TOKEN`
- **THEN** `config.settings` SHALL 使用对应的 `ES_*` 值作为 LLM 配置

## MODIFIED Requirements

### Requirement: System SHALL configure LLM centrally

系统 SHALL 在 `config/llm.py` 中提供唯一的 `init_llm()` 函数，并 SHALL 根据配置的 LLM provider 初始化全局 LLM。

#### Scenario: Ollama LLM 被设置到 Settings
- **WHEN** 使用 LLM provider `ollama` 调用 `config.llm.init_llm()`
- **THEN** `Settings.llm` SHALL 被设置为已配置的 `llama_index.llms.ollama.Ollama` 实例
- **THEN** 该实例 SHALL 使用 `config.settings` 中配置的 LLM URL 和模型名

#### Scenario: DeepSeek LLM 被设置到 Settings
- **WHEN** 使用 LLM provider `deepseek` 调用 `config.llm.init_llm()`
- **THEN** `Settings.llm` SHALL 被设置为已配置的 `llama_index.llms.openai.OpenAI` 实例
- **THEN** 该实例 SHALL 使用 `config.settings` 中配置的 DeepSeek-compatible API base URL、模型名和 token

#### Scenario: OpenAI LLM 被设置到 Settings
- **WHEN** 使用 LLM provider `openai` 调用 `config.llm.init_llm()`
- **THEN** `Settings.llm` SHALL 被设置为已配置的 `llama_index.llms.openai.OpenAI` 实例
- **THEN** 该实例 SHALL 使用 `config.settings` 中配置的 OpenAI API base URL、模型名和 token

#### Scenario: hosted provider 必须提供 token
- **WHEN** 使用 LLM provider `deepseek` 或 `openai` 调用 `config.llm.init_llm()`
- **THEN** 初始化 SHALL 要求存在非空 LLM token
- **THEN** 如果 token 缺失，初始化 SHALL 失败并返回清晰的配置错误

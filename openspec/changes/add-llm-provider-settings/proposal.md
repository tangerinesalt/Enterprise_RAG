## Why

当前项目在 `config.llm.init_llm()` 中固定把 `Settings.llm` 初始化为 Ollama 模型。如果要切换到 DeepSeek 或 OpenAI，需要修改代码，而不是只改配置。加入明确的 LLM 提供商选项后，可以把模型供应商、模型名、接口地址和 token 都收敛到 `settings.json`，同时保留 Ollama 作为本地默认方案。

## What Changes

- 在设置中新增 LLM 提供商配置，支持 `ollama`、`deepseek` 和 `openai`。
- 修改中心化 LLM 初始化逻辑，让 `config.llm.init_llm()` 根据提供商选择对应的 LlamaIndex LLM 实现。
- 当提供商缺省或为 `ollama` 时，保持当前 Ollama 行为不变。
- 为 DeepSeek 和 OpenAI 定义基于 URL、模型名和 token 的 hosted provider 配置方式。
- 本次变更不修改 embedding 配置。

## Capabilities

### New Capabilities

- 无。

### Modified Capabilities

- `model-config`：LLM 配置从仅支持 Ollama 初始化，扩展为按 provider 初始化 Ollama、DeepSeek 或 OpenAI。

## Impact

- 影响配置文件：`settings.json`、`.env.example` 或相关配置文档。
- 影响后端代码：`config/settings.py`、`config/llm.py`，以及模型初始化相关测试。
- 影响依赖：如果当前环境缺少 OpenAI-compatible LlamaIndex provider 包，需要补充对应依赖。
- 业务消费方仍然只依赖预配置好的 `llama_index.core.Settings`，不应直接实例化各 provider 客户端。

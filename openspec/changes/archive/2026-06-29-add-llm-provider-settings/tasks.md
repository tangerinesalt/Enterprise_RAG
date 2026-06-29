## 1. 配置读取

- [x] 1.1 在 `config/settings.py` 中新增 `LLM_PROVIDER`、`LLM_URL`、`LLM_MODEL` 和 `LLM_TOKEN` 导出。
- [x] 1.2 将 `LLM_PROVIDER` 标准化为 lowercase，并在缺省时默认使用 `ollama`。
- [x] 1.3 当标准 `LLM_*` 配置缺失时，继续兼容 `ES_URL`、`ES_MODEL` 和 `ES_TOKEN`。
- [x] 1.4 为 Ollama、DeepSeek 和 OpenAI 定义必要的 provider 默认值。

## 2. LLM 初始化

- [x] 2.1 更新 `config/llm.py`，根据 `LLM_PROVIDER` 选择 LlamaIndex LLM 类。
- [x] 2.2 保持 `ollama` 走 `llama_index.llms.ollama.Ollama`。
- [x] 2.3 让 `deepseek` 通过 `llama_index.llms.openai.OpenAI` 初始化，并使用配置的 API base URL、模型名和 token。
- [x] 2.4 让 `openai` 通过 `llama_index.llms.openai.OpenAI` 初始化，并使用配置的 API base URL、模型名和 token。
- [x] 2.5 对不支持的 provider 和 hosted provider 缺失 token 的情况抛出清晰配置错误。

## 3. 文档与示例

- [x] 3.1 更新 `settings.json` 示例，展示 `LLM_PROVIDER`。
- [x] 3.2 在 README 中补充 Ollama、DeepSeek 和 OpenAI 的配置示例。
- [x] 3.3 明确说明 embedding 配置不在本次变更范围内。

## 4. 验证

- [x] 4.1 增加或更新默认 Ollama provider 行为测试。
- [x] 4.2 增加或更新标准 `LLM_*` 配置键与旧 `ES_*` 别名兼容测试。
- [x] 4.3 增加或更新 DeepSeek 和 OpenAI provider 构造测试，测试不得发起真实网络请求。
- [x] 4.4 增加或更新非法 provider 和缺失 token 的错误测试。
- [x] 4.5 运行相关测试，并对 `config.init.init_models()` 做 smoke import 验证。

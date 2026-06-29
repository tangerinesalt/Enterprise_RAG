## Context

项目的运行时模型配置集中在 `config/` 下。`config/settings.py` 从项目根目录的 `settings.json` 读取配置，`config/llm.py` 初始化 `llama_index.core.Settings.llm`，业务代码通过全局 `Settings` 使用模型。

当前 LLM 初始化逻辑固定导入并构造 `llama_index.llms.ollama.Ollama`，配置来源是 `OLLAMA_URL` 和 `LLM_MODEL`。这对本地 Ollama 可用，但接入 DeepSeek 或 OpenAI 时需要改代码。现有 `settings.json` 使用的是 `ES_URL`、`ES_MODEL`、`ES_TOKEN`，这些旧字段在迁移期间仍应可用。

## Goals / Non-Goals

**Goals:**

- 新增明确的 `LLM_PROVIDER` 配置，支持 `ollama`、`deepseek` 和 `openai`。
- 当 `LLM_PROVIDER=ollama` 时，使用 `llama_index.llms.ollama.Ollama`。
- 当 `LLM_PROVIDER=deepseek` 或 `LLM_PROVIDER=openai` 时，使用 `llama_index.llms.openai.OpenAI`，并传入对应 base URL、模型名和 API key。
- 未配置 provider 时默认使用 `ollama`，保持现有本地启动体验。
- 保持消费方代码不变，provider 选择只出现在中心化配置层。

**Non-Goals:**

- 不修改 embedding provider。
- 不新增前端配置页面。
- 不支持三种指定 provider 之外的任意插件式 provider。
- 不修改会话、检索或 prompt 行为。

## Decisions

### 在 `config.llm` 中做 provider 分发

`init_llm()` 根据 `config.settings` 暴露的标准化 provider 值选择 LLM 实现。这样 provider 专属 import、参数映射和错误处理都集中在一个地方。

备选方案是为每个 provider 建独立模块，例如 `config/llms/openai.py` 和 `config/llms/ollama.py`。这个结构扩展性更强，但当前只有三个 provider 和一个初始化入口，小型内部工厂更直接，也更容易测试。

### 保持 Ollama 向后兼容

当 `LLM_PROVIDER` 缺省、为空或设置为 `ollama` 时，`Settings.llm` 继续初始化为 `Ollama` 实例，并使用现有本地默认值。`ES_URL` 和 `ES_MODEL` 继续作为 `LLM_URL` 和 `LLM_MODEL` 的兼容别名。

备选方案是强制用户立即迁移到 `LLM_*` 配置名。这样命名更清晰，但会让当前 `settings.json` 失效，收益不足。

### 将 DeepSeek 作为 OpenAI-compatible provider 接入

DeepSeek 使用 `llama_index.llms.openai.OpenAI`，通过 DeepSeek API base URL 和 API token 调用。这样不需要增加 DeepSeek 专属依赖，也符合 DeepSeek 常见的 OpenAI-compatible API 接入方式。

备选方案是引入 DeepSeek 专属 client 包。除非后续需要 DeepSeek 独有能力，否则这会增加依赖面和维护成本。

### 使用标准配置名，并保留旧别名

推荐配置名：

- `LLM_PROVIDER`
- `LLM_URL`
- `LLM_MODEL`
- `LLM_TOKEN`

兼容旧配置名：

- `ES_URL` 作为 `LLM_URL` 的 fallback
- `ES_MODEL` 作为 `LLM_MODEL` 的 fallback
- `ES_TOKEN` 作为 `LLM_TOKEN` 的 fallback

provider 默认值只在对应 provider 未显式配置时使用。Ollama 可默认使用本地无鉴权接口；OpenAI 和 DeepSeek 必须提供 token。

## Risks / Trade-offs

- provider 值非法 -> 初始化阶段快速失败，并明确列出支持的 provider。
- hosted provider 缺少 token -> 在首次对话前失败，避免请求阶段才暴露难排查错误。
- DeepSeek 的 OpenAI-compatible 行为可能与 OpenAI 存在差异 -> 首版只使用普通 chat completion 所需参数。
- `ES_*` 命名容易造成误解 -> 文档中推荐 `LLM_*`，`ES_*` 仅作为兼容别名保留。

## Migration Plan

1. 在 `config.settings` 中新增 `LLM_PROVIDER`，默认值为 `ollama`。
2. 新增标准 `LLM_*` 配置读取，同时保留 `ES_*` fallback。
3. 更新 `config.llm.init_llm()`，按 provider 初始化不同 LLM。
4. 更新示例配置和 README，展示三种 provider 的配置方式。
5. 增加聚焦测试：Ollama 默认行为、OpenAI 构造、DeepSeek 构造、非法 provider、缺失 token。

回滚方式很简单：将 `LLM_PROVIDER` 设置为 `ollama` 或删除该字段，系统应恢复为当前本地 Ollama 初始化行为。

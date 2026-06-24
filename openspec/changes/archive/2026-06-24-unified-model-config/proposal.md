## Why

目前 LLM 和 Embedding 模型的配置分散在各消费模块中：`app/kb_manager/indexer.py` 中手动创建 `OllamaEmbedding`，`test/test_retrieve.py` 中又重复创建 `OllamaEmbedding` + `Ollama`。每次更换模型（如从 Ollama 切换到 OpenAI 或 HuggingFace）需要修改多处代码，且 `Settings.embed_model` 和 `Settings.llm` 没有统一的初始化入口。

需要集中管理模型配置，所有模块通过 LlamaIndex 的全局 `Settings` 对象共享，更换模型时只需修改一处。

## What Changes

- 新增 `config/llm.py` — LLM 配置模块，初始化并设置 `Settings.llm`
- 新增 `config/embedding.py` — Embedding 配置模块，初始化并设置 `Settings.embed_model`
- 新增 `config/init.py` — 统一初始化入口，按序调用上述两个模块
- 修改 `app/kb_manager/indexer.py` — 移除内联的模型实例化代码，改用 `Settings`
- 修改 `test/test_retrieve.py` — 移除内联的模型实例化代码，改为调用 `config.init.init_models()`
- `config/settings.py` 保持不变（仍负责读取原始配置项）
- **BREAKING**: `config.settings` 不再直接导出模型实例，仅保留原始配置值

## Capabilities

### New Capabilities
- `model-config`: LLM 和 Embedding 模型的集中配置管理，通过 `config/init.py` 统一初始化

### Modified Capabilities

- `kb-ingestion`: 索引器不再自行创建 Embedding 模型，依赖全局 `Settings.embed_model`
- `kb-retrieval-test`: 测试脚本不再自行创建 LLM 和 Embedding 模型，依赖全局配置

## Impact

- 新增文件：
  - `config/embedding.py` — 封装 Embedding 模型初始化
  - `config/llm.py` — 封装 LLM 初始化
  - `config/init.py` — 统一初始化入口
- 修改文件：
  - `app/kb_manager/indexer.py` — 删除 import 和初始化代码
  - `test/test_retrieve.py` — 删除 import 和初始化代码，改为调用 `init_models()`
- 不修改：
  - `config/settings.py` — 保持原始配置项导出
  - `example/` — 不影响示例脚本

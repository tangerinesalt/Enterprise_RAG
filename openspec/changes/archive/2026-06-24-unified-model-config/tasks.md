## 1. 配置模块新增

- [x] 1.1 创建 `config/embedding.py`：`init_embedding()` 设置 `Settings.embed_model`
- [x] 1.2 创建 `config/llm.py`：`init_llm()` 设置 `Settings.llm`
- [x] 1.3 创建 `config/init.py`：`init_models()` 按序调用两者

## 2. 消费模块改造

- [x] 2.1 修改 `app/kb_manager/indexer.py`：移除 `OllamaEmbedding` 导入和 `Settings.embed_model` 设置
- [x] 2.2 修改 `test/test_retrieve.py`：移除 `OllamaEmbedding` / `Ollama` 导入和模型实例化，改为调用 `init_models()`

## 3. 验证

- [x] 3.1 运行 `python -m app.kb_manager.cli kb upload test-kb sample.txt` 确认索引正常
- [x] 3.2 运行 `python test/test_retrieve.py test-kb "内容？"` 确认检索生成正常

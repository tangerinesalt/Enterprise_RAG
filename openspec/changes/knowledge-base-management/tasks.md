## 1. 项目结构准备

- [ ] 1.1 创建 `app/kb_manager/` 模块（`__init__.py`、`cli.py`、`indexer.py`）
- [ ] 1.2 创建 `test/` 测试目录
- [ ] 1.3 更新 `.gitignore`：添加 `kb/`（知识库数据目录）
- [ ] 1.4 实现 `config/settings.py` 读取 `settings.json` 配置

## 2. 知识库核心管理 (KnowledgeBase 类)

- [ ] 2.1 实现 `KnowledgeBase` 类：封装 kb 根路径、创建/删除/列表方法
- [ ] 2.2 实现 `create(name)`：创建目录结构 `kb/<name>/files/` + `vector_db/`
- [ ] 2.3 实现 `list_all()`：列出 `kb/` 下所有知识库
- [ ] 2.4 实现 `list_files(name)`：列出知识库内文件副本

## 3. 文件上传与删除

- [ ] 3.1 实现 `upload(kb_name, file_path)`：复制文件到 `kb/<name>/files/`（同名保存）
- [ ] 3.2 实现 `delete_file(kb_name, filename)`：删除文件副本
- [ ] 3.3 实现上传时同名文件覆盖逻辑（先删原向量 → 重新索引）

## 4. 文档索引 (indexer.py)

- [ ] 4.1 实现 `Indexer` 类：封装 llama_index 的文档解析能力
- [ ] 4.2 复用 `RobustPDFReader`：支持 PDF/TXT/MD，含 OCR 兜底
- [ ] 4.3 实现 `index_file(kb_name, filename)`：解析 → 分块 → Embedding → ChromaDB
- [ ] 4.4 实现 `delete_vectors(kb_name, filename)`：按 `file_name` 元数据删除向量
- [ ] 4.5 实现 `reindex_file(kb_name, filename)`：删除旧向量 → 重新索引

## 5. CLI 入口 (cli.py)

- [ ] 5.1 实现 `argparse` 子命令解析器
- [ ] 5.2 实现 `kb create` 子命令
- [ ] 5.3 实现 `kb upload` 子命令
- [ ] 5.4 实现 `kb delete` 子命令
- [ ] 5.5 实现 `kb reindex` 子命令
- [ ] 5.6 实现 `kb list` 子命令
- [ ] 5.7 友好的错误提示和帮助文档

## 6. 测试接口 (test_retrieve.py)

- [ ] 6.1 实现 `test/test_retrieve.py`：按知识库名称加载 ChromaDB → 检索 → LLM 生成
- [ ] 6.2 支持命令行参数：`python test/test_retrieve.py <kb_name> <query>`
- [ ] 6.3 输出格式：检索片段 + 生成回答 + 来源引用

## 7. 验证测试

- [ ] 7.1 创建知识库：`python -m app.kb_manager.cli kb create test-kb`
- [ ] 7.2 上传文件：`python -m app.kb_manager.cli kb upload test-kb sample.txt`
- [ ] 7.3 测试检索：`python test/test_retrieve.py test-kb "内容是什么？"`
- [ ] 7.4 测试文件删除 + 重新上传
- [ ] 7.5 测试多知识库隔离
- [ ] 7.6 更新 `project.md` 里程碑状态

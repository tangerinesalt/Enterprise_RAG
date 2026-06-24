## 1. 项目结构准备

- [x] 1.1 创建 `app/kb_manager/` 模块（`__init__.py`、`cli.py`、`indexer.py`）
- [x] 1.2 创建 `test/` 测试目录
- [x] 1.3 更新 `.gitignore`：添加 `kb/`（知识库数据目录）
- [x] 1.4 实现 `config/settings.py` 读取 `settings.json` 配置

## 2. 知识库核心管理 (KnowledgeBase 类)

- [x] 2.1 实现 `KnowledgeBase` 类：封装 kb 根路径、创建/删除/列表方法
- [x] 2.2 实现 `create(name)`：创建目录结构 `kb/<name>/files/` + `vector_db/`
- [x] 2.3 实现 `list_all()`：列出 `kb/` 下所有知识库
- [x] 2.4 实现 `list_files(name)`：列出知识库内文件副本

## 3. 文件上传与删除

- [x] 3.1 实现 `upload(kb_name, file_path)`：复制文件到 `kb/<name>/files/`（同名保存）
- [x] 3.2 实现 `delete_file(kb_name, filename)`：删除文件副本
- [x] 3.3 实现上传时同名文件覆盖逻辑（先删原向量 → 重新索引）

## 4. 文档索引 (indexer.py)

- [x] 4.1 实现 `Indexer` 类：封装 llama_index 的文档解析能力
- [x] 4.2 复用 `RobustPDFReader`：支持 PDF/TXT/MD，含 OCR 兜底
- [x] 4.3 实现 `index_file(kb_name, filename)`：解析 → 分块 → Embedding → ChromaDB
- [x] 4.4 实现 `delete_vectors(kb_name, filename)`：按 `file_path` 元数据删除向量
- [x] 4.5 实现 `reindex_file(kb_name, filename)`：删除旧向量 → 重新索引

## 5. CLI 入口 (cli.py)

- [x] 5.1 实现 `argparse` 子命令解析器
- [x] 5.2 实现 `kb create` 子命令
- [x] 5.3 实现 `kb upload` 子命令
- [x] 5.4 实现 `kb delete` 子命令
- [x] 5.5 实现 `kb reindex` 子命令
- [x] 5.6 实现 `kb list` 子命令
- [x] 5.7 友好的错误提示和帮助文档

## 6. 测试接口 (test_retrieve.py)

- [x] 6.1 实现 `test/test_retrieve.py`：按知识库名称加载 ChromaDB → 检索 → LLM 生成
- [x] 6.2 支持命令行参数：`python test/test_retrieve.py <kb_name> <query>`
- [x] 6.3 输出格式：检索片段 + 生成回答 + 来源引用

## 7. 验证测试

- [x] 7.1 创建知识库：`python -m app.kb_manager.cli kb create test-kb`
- [x] 7.2 上传文件：`python -m app.kb_manager.cli kb upload test-kb sample.txt`
- [x] 7.3 测试检索：`python test/test_retrieve.py test-kb "内容是什么？"`
- [x] 7.4 测试文件删除 + 重新上传
- [x] 7.5 测试多知识库隔离
- [x] 7.6 更新 `project.md` 里程碑状态

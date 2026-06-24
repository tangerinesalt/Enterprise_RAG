## 1. KnowledgeBase 类 — 文件夹支持

- [x] 1.1 实现 `upload_folder(kb_name, source_dir)`：递归复制目录结构到 `files/`
- [x] 1.2 实现 `list_folder(kb_name, folder_path)`：递归列出目录下所有文件
- [x] 1.3 实现 `delete_folder(kb_name, folder_name)`：递归删除目录及内部所有文件
- [x] 1.4 修改 `list_files(kb_name)`：支持区分文件和子目录

## 2. Indexer — 批量索引

- [x] 2.1 实现 `index_folder(kb_name, folder_name)`：递归遍历目录，批量索引每个文件
- [x] 2.2 实现 `index_all(kb_name)`：索引 files/ 中所有文件（递归遍历）

## 3. CLI 命令改造

- [x] 3.1 修改 `kb upload`：不再自动索引，仅复制（支持文件和文件夹）
- [x] 3.2 新增 `kb index` 子命令（支持 file / folder / --all）
- [x] 3.3 新增 `kb upload-and-index` 子命令（上传+索引一步）
- [x] 3.4 修改 `kb delete`：支持文件夹删除（递归清理文件+向量）
- [x] 3.5 更新帮助文本和示例

## 4. 自动测试脚本

- [x] 4.1 创建 `test/test_auto.py`：桌面创建 rag-test/ 目录（A1~A4 嵌套结构）
- [x] 4.2 实现全链路：create → upload folder → index folder → query → 验证 → 清理
- [x] 4.3 每个查询验证回答包含预期关键词，输出 pass/fail

## 5. 验证

- [x] 5.1 测试 `kb upload` 单个文件（确认不再自动索引）
- [x] 5.2 测试 `kb index` 单个文件
- [x] 5.3 测试 `kb upload` 文件夹 + `kb index` 文件夹
- [x] 5.4 测试 `kb delete` 文件夹（递归清理）
- [x] 5.5 测试 `kb upload-and-index` 快捷命令
- [x] 5.6 运行 `test/test_auto.py` 全自动测试

## Why

当前 `kb upload` 同时执行文件复制和向量索引，导致上传和索引耦合。需要分离两个阶段，让用户可以批量上传后再统一索引。同时需要支持文件夹上传、文件夹删除（递归清理向量），以及提供自动测试脚本验证端到端功能。

## What Changes

- **BREAKING**: `kb upload` 不再自动索引，仅复制文件到 `files/`
- 新增 `kb index <name> <target>` — 对文件/文件夹手动触发索引
- 新增 `kb upload-and-index <name> <path>` — 上传+索引一步完成（快捷命令）
- `kb upload` 支持上传文件夹（保持目录结构，完整复制到 files/）
- `kb delete` 支持删除文件夹（递归删除所有文件 + 对应向量）
- 目录结构本身作为文件映射，无需额外映射文件
- 新增 `test/test_auto.py` — 自动测试脚本（创建测试目录 → upload → index → query → 校验 → 清理）

## Capabilities

### New Capabilities
- `cli-index-command`: `kb index` 命令，对文件/文件夹触发索引
- `cli-upload-and-index`: `kb upload-and-index` 快捷命令
- `cli-folder-support`: 文件夹上传（展平）、文件夹删除（递归）
- `auto-test`: 自动测试脚本，验证全链路

### Modified Capabilities

- `kb-management`: `kb upload` 改为仅复制（不自动索引）；`kb delete` 支持文件夹递归
- `kb-ingestion`: indexer 新增按文件夹批量索引能力

## Impact

- 修改 `app/modules/kb_manager/__init__.py` — KnowledgeBase 类增加文件夹操作和映射文件
- 修改 `app/modules/kb_manager/indexer.py` — Indexer 增加文件夹批量索引
- 修改 `app/modules/kb_manager/cli.py` — 新增 index、upload-and-index 命令；修改 upload、delete 行为
- 新增 `test/test_auto.py` — 自动测试脚本（测试完成后清理）
- 新增 `%USERPROFILE%/Desktop/rag-test/` — 测试目录（测试完成后删除）

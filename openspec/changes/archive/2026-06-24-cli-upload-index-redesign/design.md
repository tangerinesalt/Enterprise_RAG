## Context

当前 CLI 的 `kb upload` 命令同时执行文件复制和向量索引，两者耦合。用户需要在批量上传后再统一索引，也需要支持文件夹操作。

依赖关系：`cli.py` → `KnowledgeBase`（文件管理）+ `Indexer`（向量索引）。

## Goals / Non-Goals

**Goals:**
- upload 和 index 分离为两个独立命令
- 支持文件夹上传（保持目录结构，完整复制到 files/）
- 支持文件夹删除（递归清理文件 + 向量）
- 目录结构本身即为文件映射，无需额外映射文件
- 提供快捷命令 `upload-and-index`
- 自动测试脚本

**Non-Goals:**
- 不修改向量数据库结构
- 不改 config 和 example 目录

## Decisions

### 1. 文件夹上传保持目录结构

上传文件夹 `my-folder/` 时，`kb/my-docs/files/` 保留完整目录结构：

```
kb/my-docs/files/
├── report.pdf                    ← 单文件上传
└── my-folder/                    ← 文件夹上传
    ├── doc1.txt
    └── sub/
        ├── doc2.txt
        └── doc3.txt
```

- **理由**：目录结构本身就是最好的映射文件。用户查看 files/ 目录一目了然，无需额外维护 `_folder_map.json`。
- `kb upload my-docs my-folder` 只复制文件，不索引。
- `kb index my-docs my-folder` 遍历该目录下所有文件递归索引。
- `kb delete my-docs my-folder` 递归删除目录 + 遍历删除所有向量。

### 2. index 命令行为

```
kb index my-docs report.pdf        → 索引单个文件
kb index my-docs my-folder         → 遍历 kb/my-docs/files/my-folder/，递归索引
kb index my-docs --all             → 索引 files/ 中所有文件（递归）
```

索引时跳过常见的临时文件（`.DS_Store`、`Thumbs.db` 等）。

### 3. delete 文件夹行为

```
kb delete my-docs my-folder
→ 1. 递归扫描 kb/my-docs/files/my-folder/ 获取所有文件
→ 2. 对每个文件调用 delete_vectors + remove_file
→ 3. 删除 kb/my-docs/files/my-folder/ 目录
```

如果 delete 的是单个文件，行为不变（删文件 + 删向量）。

### 4. test_auto.py 流程

```
1. 创建 %USERPROFILE%/Desktop/rag-test/（A1~A4 嵌套结构）
2. kb create auto-test
3. kb upload auto-test %Desktop%/rag-test/
4. kb index auto-test rag-test
5. 依次查询 A1~A4，验证回答包含预期关键词
6. kb delete auto-test rag-test（递归清理）
7. kb delete auto-test（删除知识库）
8. 删除桌面 rag-test/ 目录
9. 输出测试报告
```

测试数据目录结构：

```
%USERPROFILE%/Desktop/rag-test/
├── A1-概述.txt         → 内容回答"什么是A1？"
├── A2-原理.txt         → 内容回答"什么是A2？"
└── sub/
    ├── A3-应用.txt     → 内容回答"什么是A3？"
    └── A4-实践.txt     → 内容回答"什么是A4？"
```

## 文件变更

```
app/modules/kb_manager/
├── __init__.py    修改 → 新增文件夹递归操作
├── cli.py         修改 → 新增 index / upload-and-index 命令；修改 upload / delete
└── indexer.py     修改 → 新增按目录递归索引

test/test_auto.py  新增 → 自动测试脚本
```

## Risks / Trade-offs

- **[风险] 深层嵌套目录** → index 和 delete 时递归遍历，不影响逻辑复杂性
- **[风险] files/ 目录混合文件和文件夹** → knowledge_base.list_files() 需要区分文件和文件夹，支持递归或非递归

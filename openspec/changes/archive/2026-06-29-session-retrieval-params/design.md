## Context

当前会话 `config.json` 仅存储 `{kb_name, active_chat}`，检索参数 `top_k`（向量/BM25 召回数）和 `top_n`（重排序保留数）在 `app/modules/retrieval/retriever.py` 和 `app/modules/session/session_manager.py` 中硬编码为固定值（top_k=5, top_n=3）。所有会话共享同一套参数，无法按需调整。

## Goals / Non-Goals

**Goals:**
- 会话创建时 `config.json` 自动写入 `top_k=8, top_n=5`
- CLI 可查看和修改会话的检索参数
- REST API 可查看和修改会话的检索参数
- 聊天（chat + chat_stream）从 config 读取参数，传递给 retriever 和 reranker
- 旧会话 config（缺 `top_k`/`top_n`）自动回退默认值，不破坏现有数据

**Non-Goals:**
- 全局默认值可配置化（仍从 `settings.json` 或代码常量读取，本次不新增配置层级）
- 参数校验以外的复杂权限控制
- 前端编辑 UI 不在本阶段范围（仅需 API 就绪，前端可选跟进）

## Decisions

### 1. 参数存放位置：会话 config.json

`config.json` 已承载会话级配置（`kb_name`, `active_chat`），扩展 `top_k`/`top_n` 字段最自然。  
**替代方案考虑**：
- 单独 params.json 文件 → 增加文件数量和代码复杂度，不必要
- 全局 settings.json → 不满足"按会话独立"的需求
- 数据库存储 → 本项目使用文件系统存储，无数据库

### 2. build_retriever 增加 top_k 参数

当前 `build_retriever` 内部硬编码 `similarity_top_k=5`，改为接收可选参数。  
同时 `_rrf_fusion` 函数也接收 `top_k`，形成完整的参数传递链。  
**理由**：最小化对外改动，retriever 模块保持无状态函数风格。

### 3. reranker top_n 由调用方传入

SessionManager 当前在 `chat()` 和 `chat_stream()` 内部创建 `SentenceTransformerRerank(top_n=3)`，改为从 config 读取值后传入。  
**理由**：reranker 是一个 postprocessor 实例，在 query_engine 构造时传入，生命周期在 session 层管理。

### 4. 默认值处理

新增常量 `DEFAULT_TOP_K = 8` 和 `DEFAULT_TOP_N = 5` 在 `SessionManager` 类中。  
读取 config 时若 `top_k`/`top_n` 不存在或非正整数，使用默认值。  
`_save_config` 写入时始终包含这两个字段。

### 5. CLI 设计：`session config <name>` 子命令

```
session config <name>                    # 展示当前参数
session config <name> --set top_k=10     # 修改单参数
session config <name> --set top_k=10 --set top_n=5  # 修改多参数
```

选择 `--set key=value` 风格而非子命令 `--top-k 10`，方便未来扩展新参数而不改 CLI 代码。

### 6. API 设计

```
GET  /api/session/{name}          ← 返回信息中新增 top_k, top_n（已有此路由）
PATCH /api/session/{name}/config  ← 新增，接受 {"top_k": 10, "top_n": 5}
```

PATCH 只接受 body 中出现的字段，未出现字段保持原值不变。

## Risks / Trade-offs

- **[兼容性] 旧会话 config.json 无 top_k/top_n 字段** → 读取时做缺失检测回退默认值，无需迁移脚本
- **[边界值] 参数设为 0 或负数** → 保存前校验 `top_k >= 1` 且 `top_n >= 1`，否则拒绝
- **[前端暂缺]** → API 层面先就绪，前端编辑 UI 列为可选后续任务

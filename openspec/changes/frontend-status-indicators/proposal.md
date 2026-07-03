## Why

当前前端在对话和知识库索引过程中完全没有可视化的操作状态反馈。发送消息后用户只能等待文本逐字出现，无法区分是在检索还是生成；索引文件时按钮无状态变化，看不到索引进度，不知道哪些文件已索引、哪些正在索引中。这些缺失的反馈降低了用户对系统行为的理解和对进度的感知。

## What Changes

### 1. 对话状态指示器

- **后端**：在 SSE 事件流中新增 `phase` 事件，标记 `retrieving`（检索）和 `generating`（生成）两个阶段的分界
- **前端**：在助手消息区域下方显示单行状态文字（与消息内容有明显视觉区分），按阶段显示 `⏳ Searching...` → `✏️ Generating...`，完成后自动消失

### 2. 知识库索引状态 — SSE 流式进度 + 绿色填充

- **后端**：
  - 新增 SSE 流式索引端点 `POST /api/kb/index/stream`，逐 chunk 报告 embedding 进度
  - `Indexer.index_file()` 改造为 generator：先预计算每个 chunk 的 embedding 并 `yield` 进度事件，`VectorStoreIndex` 复用预计算的 embedding（`node.embedding` 已设置时跳过重算）
  - 保留 `.index_status.json` 持久化文件存储最终状态（哪些文件已索引），`GET /api/kb/{name}` 返回此状态
- **前端**：
  - 每个文件行下方显示绿色填充进度条：`pending` 时空灰色 → `indexing` 时绿色从左到右渐增 → `indexed` 时全绿
  - 进度条显示百分比和 chunk 计数（如 "68% 索引中 (34/50 chunks)"）
  - "索引全部"显示整体进度条汇总

### 不做的事

- 不改变对话消息的渲染结构（MarkdownMessage 不变）
- 不改变后端检索或生成的逻辑
- 不添加轮询或 WebSocket——索引进度通过 SSE 推送

## Capabilities

### New Capabilities

- `chat-status-indicator`: 对话进行中的阶段状态显示（Searching... / Generating...）
- `kb-index-status`: 知识库文件索引实时进度（SSE 流式 + 绿色填充进度条）

### Modified Capabilities

- `session-chat`：SSE 事件协议新增 `phase` 事件类型
- `ui-session-page`：聊天区域新增状态指示器渲染
- `ui-kb-page`：文件列表每行新增绿色填充进度条；索引按钮保留三种操作状态

## Impact

| 模块 | 影响 |
|---|---|
| `app/modules/session/session_manager.py` | SSE generator 在检索前/生成前各 emit 一个 `phase` 事件 |
| `app/modules/kb_manager/indexer.py` | `index_file()` 改造为 generator，预计算 embedding 时逐 chunk 报告进度 |
| `app/modules/kb_manager/knowledge_base.py` | 新增 `.index_status.json` 读写方法，用于持久化索引完成状态 |
| `app/api/routers/kb.py` | 新增 `POST /kb/index/stream` SSE 端点；`GET /kb/{name}` 返回文件的 `indexed` 状态 |
| `ui/src/api/index.ts` | SSE 解析新增 `phase` 和 `index_progress` 事件处理 |
| `ui/src/components/ChatArea.tsx` | 新增对话状态指示器 |
| `ui/src/pages/KbDetail.tsx` | 文件行新增绿色填充进度条；"索引全部"显示汇总进度 |
| `ui/src/pages/KbDetail.module.css` | 新增进度条样式（绿色渐变填充） |
| `ui/src/pages/SessionChat.module.css` | 新增状态指示器样式 |

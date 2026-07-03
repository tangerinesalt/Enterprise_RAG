## 1. 后端：SSE phase 事件

- [x] 1.1 在 `session_manager.py` `chat_stream()` 中，检索前添加 `yield {"type": "phase", "phase": "retrieving"}`
- [x] 1.2 在检索完成、LLM 生成前添加 `yield {"type": "phase", "phase": "generating"}`

## 2. 前端：对话状态指示器

- [x] 2.1 在 `api/index.ts` `chatStream` 中新增 `onPhase` 回调参数和 `phase` 事件解析
- [x] 2.2 在 `ChatArea.tsx` 中新增 `phaseText` 状态，根据 `retrieving`/`generating` 显示不同文案
- [x] 2.3 在 `ChatArea.module.css` 或 `SessionChat.module.css` 中定义 `.statusLine` 样式（灰色斜体小字）
- [x] 2.4 `onDone`/`onError` 时清除状态文字

## 3. 后端：SSE 流式索引端点 + 预计算 embedding

- [x] 3.1 `Indexer` 新增 `index_file_stream()` generator 方法：chunk 化后逐 chunk 预计算 embedding 并 `yield` `index_progress`，最后构建 `VectorStoreIndex` 并 `yield index_done`
- [x] 3.2 在 `kb.py` 中新增 `POST /api/kb/index/stream` SSE 端点，返回 `StreamingResponse`
- [x] 3.3 `Indexer.index_all()` 和 `index_folder()` 增加 stream 版本，依次处理每个文件并将事件合并到一个 SSE 流
- [x] 3.4 保留原有同步 `POST /api/kb/index` 端点（内部可复用 stream 方法取最终结果，或保持独立）

## 4. 后端：索引状态持久化文件

- [x] 4.1 `KnowledgeBase` 类新增 `_index_status_path()`、`_load_index_status()`、`_save_index_status()` 私有方法
- [x] 4.2 `KnowledgeBase` 新增 `set_file_status()`、`get_file_status()`、`remove_file_status()` 公开方法
- [x] 4.3 在 `index_file_stream()` 的 `index_done` 时调用 `set_file_status("indexed", chunks)`
- [x] 4.4 `GET /api/kb/{name}` 返回的每个 file 对象增加 `indexed` 和 `chunks` 字段
- [x] 4.5 删除文件时调用 `remove_file_status()`

## 5. 前端：绿色填充进度条

- [x] 5.1 `api/index.ts` 新增 `kbApi.indexStream()` 方法，建立 SSE 连接并解析 `index_start`/`index_progress`/`index_done` 事件
- [x] 5.2 `KbDetail.tsx` 新增 `indexingProgress` 本地状态 (`Record<string, {current, total}>`)，SSE 事件驱动更新
- [x] 5.3 文件行渲染进度条 UI：外容器 6px 高灰色背景 + 内层绿色填充 `<div>`（`transition: width 0.3s ease`）
- [x] 5.4 文件行按钮三态：`pending` 蓝色/可点击、「索引」 → `indexing` 灰色/禁用、「索引中」 → `indexed` 绿色/可点击、「✓ 已索引」
- [x] 5.5 "索引全部"按钮显示汇总进度（`doneFiles/totalFiles`），任意文件索引中时禁用
- [x] 5.6 索引按钮点击后切换到 SSE 流式模式，进度完成或出错后回退到 REST 状态

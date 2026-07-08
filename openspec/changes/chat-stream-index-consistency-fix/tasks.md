## 1. 聊天流生命周期安全

- [x] 1.1 添加后端集成测试覆盖流取消的 API 级行为（取消的流不遗留副产物、不阻塞后续操作）
- [x] 1.2 更新 `ui/src/pages/SessionChat.tsx`，使聊天切换在本地选中变更前取消过时的正在进行的流
- [x] 1.3 更新当前聊天删除流程，使删除选中聊天在替换视图选定前取消过时的流

## 2. KB 进度状态恢复

- [x] 2.1 添加后端回归测试覆盖 KB 索引失败时 `.index_status.json` 的状态正确性；前端进度恢复行为手动验证
- [x] 2.2 更新 `ui/src/pages/KbDetail.tsx`，在收到 SSE `index_error` 事件时清除每文件进度状态（包括 `handleIndex` 和 `handleIndexAll` 的 `onError` 回调）；`handleIndexAll` 的 `onError` 也需调用 `load()`
- [x] 2.3 更新单文件和批量索引流程，在请求级失败时清除乐观进度和 `isIndexingAll`；用 try/catch 包裹 `await kbApi.indexStream()` 调用，防止 fetch 级别错误导致状态永久卡住

## 3. 同步与流式索引状态一致性

- [x] 3.1 添加后端回归测试，证明同步和流式索引持久化相同的文件级 `indexed/chunks` 语义（含 `len(nodes)` 验证）
- [x] 3.2 修改 `app/modules/kb_manager/indexer.py`：
  - `index_file()`: `return len(nodes)` 替代 `return collection.count()`，新增 `set_file_status()` 调用
  - `index_file_stream()`: `chunk_count = len(nodes)` 替代 `chunk_count = collection.count()`
  - 两个函数均在 `indexed` 状态中持久化文件级 `chunks` 值

## 4. 验证

- [x] 4.1 运行后端自动化测试覆盖聊天生命周期、KB 索引状态一致性和状态文件正确性
- [x] 4.2 手动验证前端流取消行为（切换聊天、删除当前聊天时旧流不残留 token）和 KB 进度恢复（SSE 错误、网络错误后进度不复位）
- [x] 4.3 重新检查变更工件是否一致，确认变更已准备好执行 `/opsx:apply`

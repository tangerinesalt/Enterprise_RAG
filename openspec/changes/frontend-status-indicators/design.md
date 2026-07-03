## Context

当前 SSE 流事件序列为：`start` → (静默检索) → `token`×N → `sources` → `done`。在 `start` 和首个 `token` 之间没有区分检索阶段和生成阶段的事件，前端无法向用户展示当前处于哪个阶段。

知识库文件索引方面，`GET /api/kb/{name}` 返回 `files[]` 数组，每个文件只有 `name`/`size`/`type`，没有索引状态字段。索引过程是一个同步的 POST 请求，完成后返回结果，但前端无法获知哪些文件已索引、更无法看见 embedding 的逐 chunk 进度。

经验证，`llama_index.core.indices.utils.embed_nodes()` 中，当 `node.embedding is not None` 时跳过调用 embed 模型，直接复用预计算值。这使"先逐 chunk 计算 embedding 报告进度，再批量构建 VectorStoreIndex"的方案可行。

## Goals / Non-Goals

**Goals:**
- 对话过程中在助手气泡下方显示阶段状态行：`⏳ Searching...` → `✏️ Generating...` → 自动消失
- 知识库文件列表每行显示绿色填充进度条，索引过程中绿色从左向右渐增
- 进度条显示百分比和 chunk 计数
- 索引状态持久化到磁盘，重启服务后保持
- 所有变更向后兼容 — 旧版前端忽略新事件，新版前端在没有状态文件时降级

**Non-Goals:**
- 不改变 LLM 调用流程或检索策略
- 不引入轮询或 WebSocket——索引进度通过 SSE 推送
- 不做批量索引的队列并发控制（当前为同步单线程）

## Decisions

### D1: SSE 新增 `phase` 事件而非改变现有事件（同前）

```python
yield {"type": "start", "chat_file": chat_file}
yield {"type": "phase", "phase": "retrieving"}
# ...检索+重排序...
yield {"type": "phase", "phase": "generating"}
# ...token 流...
yield {"type": "sources", "sources": [...]}
yield {"type": "done", "chat_file": chat_file}
```

### D2: SSE 流式索引端点 `/api/kb/index/stream`

新增端点，返回 `StreamingResponse(generator(), media_type="text/event-stream")`。

SSE 事件协议：

```
event: index_start\ndata: {"file": "report.pdf", "total_chunks": 50}\n\n
event: index_progress\ndata: {"file": "report.pdf", "current": 15, "total": 50, "pct": 30}\n\n
event: index_progress\ndata: {"file": "report.pdf", "current": 16, "total": 50, "pct": 32}\n\n
...
event: index_done\ndata: {"file": "report.pdf", "chunks": 50}\n\n
```

| 事件 | 触发时机 |
|---|---|
| `index_start` | chunk 化完成，已知 total_chunks，开始 embedding |
| `index_progress` | 每个 chunk 完成 embedding |
| `index_done` | 文件所有 chunk 处理完毕，VectorStoreIndex 构建完成 |

`Indexer` 改造为接受 callback 的 generator 模式：

```python
# indexer.py
def index_file_stream(self, kb_name: str, filename: str):
    """Generator：逐 chunk 产出进度事件"""
    _kb.set_file_status(kb_name, filename, "indexing")
    yield {"type": "index_start", "file": filename, "total_chunks": len(nodes)}
    
    embed_model = Settings.embed_model
    for i, node in enumerate(nodes):
        text = node.get_content(metadata_mode=MetadataMode.EMBED)
        node.embedding = embed_model.get_text_embedding(text)
        pct = round((i + 1) / len(nodes) * 100)
        yield {"type": "index_progress", "file": filename, "current": i + 1, "total": len(nodes), "pct": pct}
    
    # VectorStoreIndex 复用预计算 embedding（已验证 node.embedding 非 None 时跳过重算）
    index = VectorStoreIndex(nodes=nodes, storage_context=storage_context)
    
    _kb.set_file_status(kb_name, filename, "indexed", chunks=collection.count())
    yield {"type": "index_done", "file": filename, "chunks": collection.count()}
```

已有 REST 端点 `POST /api/kb/index` 保持不变（内部可复用 `index_file_stream` 仅取最终结果）。

### D3: 绿色填充进度条 UI

每个文件行在文件名下方显示一个 6px 高的进度条：

```
┌──────────────────────────────────────────────────┐
│ 📄 report.pdf                        12.3KB       │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░ 68% 索引中 (34/50)    │  ← 绿色填充 #22c55e
│ [索引中⋯]                                          │  ← 灰色禁用态
├──────────────────────────────────────────────────┤
│ 📄 manual.docx                         2.1MB       │
│ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ 100% ✓ 已索引       │  ← 全绿
│ [✓ 已索引]                                         │  ← 绿色可点击
├──────────────────────────────────────────────────┤
│ 📄 notes.txt                             512B       │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 0% 待索引          │  ← 浅灰空条
│ [索引]                                             │  ← 蓝色可点击
└──────────────────────────────────────────────────┘
```

进度条颜色使用 Tailwind 绿色系（`#22c55e` / `#16a34a`），通过 CSS 变量 `--color-index-progress` 控制。进度条宽度通过内联 `style={{ width: `${pct}%` }}` 设置。

填充动画：CSS `transition: width 0.3s ease` 使进度平滑过渡。

### D4: `.index_status.json` 持久化最终状态

状态文件仅持久化 **最终状态**（`pending` / `indexed`），不再包含 `indexing` 中间态（中间态通过 SSE 事件实时推送）。

```json
{
  "files": {
    "report.pdf": {
      "status": "indexed",
      "chunks": 50,
      "indexed_at": "2026-07-03T10:30:00"
    },
    "manual.docx": {
      "status": "indexed",
      "chunks": 128,
      "indexed_at": "2026-07-03T10:32:00"
    },
    "notes.txt": {
      "status": "pending",
      "chunks": null,
      "indexed_at": null
    }
  }
}
```

`GET /api/kb/{name}` 返回的 `files[]` 中每个元素包含：
- `indexed`: `"pending"` 或 `"indexed"`（SSE 流开始时前端自行管理 `"indexing"` 状态）
- `chunks`: 已索引文件的 chunk 数量
- `indexed_at`: 索引时间

### D5: 前端索引状态管理

前端维护一个本地状态 `indexingProgress: Record<string, {current: number, total: number}>`：

1. 页面加载时从 `GET /api/kb/{name}` 获取持久化状态（`pending`/`indexed`）
2. 发起索引时连接 SSE，收到 `index_start` 将文件标记为 `indexing`
3. 收到 `index_progress` 更新进度百分比
4. 收到 `index_done` 将文件标记为 `indexed`，清除进度
5. 多个文件按序索引时，SSE 事件流依次包含各文件的 progress 事件

"索引全部"的汇总进度 = 所有文件的 `current/total` ∑。

### D6: 对话状态指示器 UI 设计（同前）

```
┌─────────────────────────────────────┐
│ 🤖 助手                             │
│                                     │
│ 这是回答内容...                       │
│                                     │
│ ─── 来源 (3) ───                    │
│                                     │
│ ⏳ Searching...     ← 灰色斜体小字    │
└─────────────────────────────────────┘
```

样式：`font-size: 12px`、`color: #9ca3af`、`font-style: italic`、`padding: 4px 0`。

## Risks / Trade-offs

| 风险 | 缓解 |
|---|---|
| 每个 chunk 单独调用 embed_model 比批量调用慢（无 batching） | `get_text_embedding()` 内部可能已有微型 batch 或缓存。如果实测性能下降 >30%，可改为 `get_text_embedding_batch()` 每批次 16 条 + 批间 yield progress |
| `.index_status.json` 与 ChromaDB 数据不一致 | 状态文件权威性低于 ChromaDB；检测到无向量数据但状态为 `indexed` 时降级为 `pending` |
| SSE 流式索引期间用户刷新页面 → 进度丢失 | 状态文件中已持久化的 `indexed` 文件不受影响；正在索引的文件在刷新后回到 `pending`，可重新索引 |
| 大型文件（数百 chunk）进度事件过于密集 | 每 chunk 都发事件，SSE 可能被淹没。可改为每 5% 或每 5 chunk 发一次进度事件 |

## Open Questions

1. 单 chunk embedding 耗时通常在 50-200ms，对于 50 个 chunk 的文件，进度条约 2.5-10 秒完成填充——这个节奏对用户是否合适？如果太慢，考虑 batch embedding（`get_text_embedding_batch` 每次 16 条）降低总耗时。

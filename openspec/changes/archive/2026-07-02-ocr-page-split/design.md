## Context

当前 OCR 路径的代码流程：

```
RobustPDFReader.load_data()
  ├─ pypdf 逐页提取 → docs = [(text, page_num), ...]
  │   └─ 如果提取文本过少（空页占比 >50% 或总字数 <50）
  │       └─ _ocr_pdf(file_path) → str        ← 合并所有页
  │           └─ return [Document(text=单页字符串, page_label="ocr")]
  └─ 正常情况 → 逐页 Document
```

问题：OCR 路径把 N 页合并为 1 个 Document，后续管线无法区分页面边界。

## Goals / Non-Goals

**Goals:**
- OCR 路径改为逐页返回 Document，与 pypdf 路径行为一致
- `page_label` 元数据标识 OCR 来源及页码
- 不改变 OCR 的识别方式（仍然使用 pypdfium2 + RapidOCR）
- 不影响 pypdf 直接提取的路径

**Non-Goals:**
- 不涉及分块参数或检索逻辑的修改
- 不做版面分析或表格重建
- 不改动 `page_label` 为 `"ocr"` 的已有索引数据（重索引时会自然更新）

## Decisions

### Decision 1：`_ocr_pdf()` 返回类型从 `str` 改为 `list[str]`

**选择**：修改 `_ocr_pdf()` 返回逐页文本列表，而非合并字符串。

**理由**：
- 调用方 `RobustPDFReader.load_data()` 需要按页创建 Document
- 返回列表比返回带分隔符的字符串更清晰，避免了分隔符可能出现在 OCR 文本中的问题
- pypdfium2 已经是逐页渲染的，只是返回前做了合并

```python
# 修改前
def _ocr_pdf(file_path: str) -> str:
    ...
    return "\n".join(all_lines)

# 修改后
def _ocr_pdf(file_path: str) -> list[str]:
    ...
    return ["\n".join(page_lines) for page_lines in page_results]
```

### Decision 2：OCR 页标签格式

**选择**：使用 `"ocr_p1"`、`"ocr_p2"` 格式。

**理由**：
- 与 pypdf 路径的 `"p1"`、`"p2"` 区分，便于调试时识别文本来源
- 格式一致，可以统一解析页码数字

### Decision 3：空页处理

**选择**：OCR 后仍然会有空页（纯空白页、分隔页）。与 pypdf 路径一致——保留空页的 Document 但文本为空字符串，让下游 `chunk_documents()` 和 SentenceSplitter 自行过滤。

**理由**：
- 保持两种路径行为一致
- `chunk_documents()` 中的 `strip_page_repeats()` 需要知道总页数（含空页）来做跨页检测
- SentenceSplitter 自然会跳过空文本的节点

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| OCR 性能不变——渲染和识别次数不变，只是返回结构变化 | 无需缓解 |
| 向量数可能增加（单页大 chunk 被拆为多页小 chunk） | 这是预期行为，重索引后可对比验证 |
| 原有索引数据中的 `page_label: "ocr"` 与新数据的 `"ocr_p1"` 不兼容 | 重索引后自动更新，无需兼容旧数据 |

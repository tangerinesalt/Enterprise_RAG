## Why

当前 OCR 兜底路径 `_ocr_pdf()` 使用 pypdfium2 逐页渲染 + RapidOCR 识别后，将所有页的文本合并为**单个 Document**：

```python
# 当前行为
return [Document(text=ocr_text, metadata={"page_label": "ocr"})]
# 整个 PDF 只有 1 个 Document，丢失了页边界
```

这导致了两个问题：

1. **页眉页脚去重失效** — `strip_page_repeats()` 依赖跨页检测，但 OCR 文档只有 1 个"页"，检测被跳过
2. **逐页元数据丢失** — 无法知道某段文本来自第几页，不利于溯源和后续版面分析

将 OCR 输出改为按页返回 Document，即可让后续管线（分块、去重、检索）获得正确的页面视图。

## What Changes

- 修改 `_ocr_pdf()` 返回逐页 OCR 结果而非合并文本
- 修改 `RobustPDFReader.load_data()` 中 OCR 兜底路径，为每页创建独立的 Document，`page_label` 设为 `"ocr_p1"`、`"ocr_p2"` 等形式
- 不修改 pypdf 直接提取的路径（已按页返回 Document）
- 行为不变：索引器接收到的 Document 列表仍然逐页，只是现在 OCR 文档的页面数正确了

## Capabilities

### New Capabilities
- `ocr-page-split`: OCR 管线保留 PDF 页边界，逐页返回识别结果

### Modified Capabilities
<!-- 无接口级行为变更，属于内部实现优化 -->

## Impact

| 范围 | 影响 |
|------|------|
| `app/modules/kb_manager/indexer.py` | 修改 `_ocr_pdf()` 返回值和 `RobustPDFReader.load_data()` 的 OCR 路径 |
| `app/modules/kb_manager/chunker.py` | 无需修改（它已经处理多页 Document 列表） |
| 向量索引 | OCR 文档的向量数会变化（从单页大 chunk 变为多页小 chunk），需要重索引 |
| API 契约 | 无变化 |
| 前端 | 无变化 |

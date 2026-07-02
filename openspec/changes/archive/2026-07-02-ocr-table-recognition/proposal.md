## Why

当前管线对扫描件 PDF（13/14 文件）的表格识别能力为零：

```
扫描件 PDF → pypdfium2 渲染 → RapidOCR 纯文本识别 → 表格结构全部丢失
```

已有的 `pdf-table-extraction` 方案只解决了 pypdf 可提取文档的表格问题，对扫描件无效。印章审批矩阵、费用标准表、文件登记表等扫描件中的表格数据在检索中只能匹配零散关键词，无法回答"哪个部门审批哪类印章"这类依赖列结构的问题。

**RapidTable（RapidAI 组织出品）** 提供基于 ONNX Runtime 的表格结构识别能力，与已有的 RapidOCR 共用推理底座，无需引入 PaddlePaddle 等重型框架。实测在扫描件权限矩阵页上成功将平铺文本还原为结构化 HTML 表格。

## What Changes

- 在现有 OCR 路径旁新增 **RapidTable 表格识别** 选项
- 渲染后的页面图片先送 RapidTable 做表格结构检测
- 含表格的页面 → 输出 HTML 表格 + 单元格文本 → 转为 Markdown 格式
- 无表格的页面 → 走 RapidOCR 普通文本识别（保持现有流程）
- **RapidTable 作为可选增强**，不是 RapidOCR 的替代——由配置控制启用

**不涉及的变化：**
- 不修改分块、检索、生成等下游环节
- 不影响 pypdf 直接提取的路径
- 不改变已有的 OCR 逐页 Document 结构

## Capabilities

### New Capabilities
- `ocr-table-recognition`: 扫描件 OCR 管线中新增表格结构识别，将表格还原为 HTML/Markdown 格式

### Modified Capabilities
- `kb-ingestion`: OCR 兜底路径新增 RapidTable 表格识别步骤

## Impact

| 范围 | 影响 |
|------|------|
| `app/modules/kb_manager/indexer.py` | `_ocr_pdf()` 或新增 `_ocr_pdf_tables()` 分支 |
| 依赖 | `rapid-table` + slanet-plus.onnx 模型（首次自动下载 7.4MB） |
| 性能 | 含表格页面 ~3s/页，纯文本页面 <1s/页（无额外开销） |
| RapidOCR 路径 | 不受影响，共存 |
| 已有索引 | 需重索引后生效 |

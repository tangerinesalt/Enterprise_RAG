## Why

当前管线中，PDF 中的表格数据在提取过程中完全丢失了结构：

- **pypdf.PdfReader.extract_text()** 将表格内容拆成散列的文本片段，行列关系丢失
- **RapidOCR** 对扫描件同样只输出文字序列，不识别表格边界

结果是：权限审批矩阵变成了散列的短行列表，修订记录表变成了空格分隔的文本行。这些内容虽然还能被检索到个别关键词，但无法回答"哪个部门审批哪类印章"这种依赖列关系的问题。

## What Changes

- 在 `RobustPDFReader` 中新增 **pdfplumber** 表格抽取路径，作为 pypdf 提取的上游或补充
- 抽取到的表格转为 **Markdown 格式**（`| col1 | col2 |`）嵌入对应页面的 Document 文本中
- 非表格文本仍走现有 pypdf 提取路径
- 扫描件（OCR）的表格提取暂不涉及——先解决 pypdf 可提取文档的表格问题

**不涉及的变化：**
- 不分拆 Document——表格数据合并到同页文本中，维持按页 Document 结构
- 不修改 chunker 或检索逻辑——表格作为 Markdown 文本进入分块和嵌入，检索时自然命中

## Capabilities

### New Capabilities
- `pdf-table-extraction`: 在文档解析阶段自动检测并格式化 PDF 中的表格，输出为 Markdown 格式

### Modified Capabilities
- `kb-ingestion`: 文档解析步骤新增表格抽取阶段，影响解析产出格式

## Impact

| 范围 | 影响 |
|------|------|
| `app/modules/kb_manager/indexer.py` | `RobustPDFReader` 新增 pdfplumber 调用和表格合并逻辑 |
| 依赖 | 新增 `pdfplumber`（纯 Python，无外部系统依赖） |
| 扫描件 OCR 路径 | 不影响（pdfplumber 对无文本 PDF 返回空结果，自然跳过） |
| 已有索引 | 需对相关 KB 重索引后生效 |
| API/前端 | 无变化 |

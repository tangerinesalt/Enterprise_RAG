## Why

当前 chunker 对 Markdown 表格的切分是无感知的。SentenceSplitter 按句子边界断开文本，但表格的语义边界是列头分离线（`---|---|---`）和行结构，不是自然语言句子。

诊断显示：权限审批矩阵页（845 chars）被切为 3 个 node，其中 2 个是 **"孤儿碎片"**——有单元格数据和管道符，但列头分离线 `---|---|---` 被切到上一个 node，丢失了列对应关系。

当 LLM 拿到这些碎片时，无法区分 `公章` 是"印章名称"列的值还是"使用部门"列的值。结构化表格的结构优势被 chunk 切割抵消了。

## What Changes

- 在 `chunk_documents()` 中新增**表格边界感知**预处理步骤
- 对每页文本做表格区域检测（查找 `|---|` 标记的 Markdown 表格边界）
- **两个子策略：**
  1. **小表保护**：对于可放入单 chunk 的表格，标记其边界为"不可切分"，强制保持完整
  2. **大表补头**：对于超过 chunk_size 的表格，在每个碎片 node 前面自动补全列头（`| col1 | col2 |` + `|---|---|`）

**不涉及的变化：**
- 不修改索引、OCR、检索等下游环节
- 不改变已有表格抽取逻辑（pdfplumber + RapidTable）
- 不改动 SentenceSplitter 本身——在其前后做处理

## Capabilities

### New Capabilities
- `table-aware-chunking`: 在文本分块时感知 Markdown 表格边界，保护表格结构完整性

### Modified Capabilities
- `kb-ingestion`: 分块策略新增表格边界感知步骤

## Impact

| 范围 | 影响 |
|------|------|
| `app/modules/kb_manager/chunker.py` | `chunk_documents()` 新增表格边界保护和补头逻辑 |
| 已有索引 | 需重索引后生效（但 chunk 变化不破坏向后兼容） |
| 下游检索/LLM | 无影响——node 格式不变，只是内容更完整 |

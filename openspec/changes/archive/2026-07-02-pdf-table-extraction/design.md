## Context

当前 `RobustPDFReader.load_data()` 的流程：

```
1. pypdf.PdfReader 逐页提取文本
2. 检测每页文本量：
   ├─ 文本足够 → 返回 [(text, page_num), ...]
   └─ 文本不足 → _ocr_pdf() 逐页 OCR
3. 每页转为 Document → chunker
```

全程没有表格识别。即使 `pypdf` 提取到了修订记录表的文字 "B/0 2023.6.1 全文 改版新订"，结构信息（哪列是版本、哪列是日期）也丢失了。

目标：对于 pypdf 可提取的 PDF，插入 `pdfplumber` 做结构化表格抽取，将表格转为 Markdown 格式合并到同页文本中。

## Goals / Non-Goals

**Goals:**
- 对 pypdf 可提取的 PDF，检测并提取表格结构
- 表格转为 Markdown 格式 `| col1 | col2 |`，嵌入对应页的 Document 文本
- 保持按页 Document 结构不变
- 对扫描件 PDF（无文本层）透明跳过

**Non-Goals:**
- 不做扫描件的表格识别（需要 PaddleOCR 级别版面分析，属于另一提案）
- 不修改 chunker 或检索参数
- 不生成独立的表格 Document——表格数据合并在同页文本中
- 不做跨页表格合并（复杂度过高，第一版不考虑）

## Decisions

### Decision 1：使用 pdfplumber，不引入 camelot/tabula

**选择**：只用 `pdfplumber`，排除 camelot 和 tabula。

**理由**：
| 工具 | 需要外部依赖 | 扫描件支持 | 安装复杂度 |
|------|------------|-----------|-----------|
| pdfplumber | 无 | ❌ | `pip install pdfplumber` |
| camelot | ghostscript | ❌ | Windows 下 ghostscript 安装麻烦 |
| tabula | Java | ❌ | 需要 JRE 环境 |

当前代码库只有 `pip install pdfplumber` 的额外开销，而且是 pure Python，对 CI/CD 和部署友好。

### Decision 2：表格输出为 Markdown 格式，嵌入页面文本

**选择**：pdfplumber 的 `extract_tables()` 返回 `list[list[str]]`，转为这种格式嵌入 Document：

```
| 版本 | 修订日期 | 修订内容 | 修订人 |
|------|---------|---------|--------|
| B/0 | 2023.6.1 | 全文改版新订 | 人力资源部 |
| B/1 | 2024.3.1 | 迟到判定30→20分钟 | 人力资源部 |
```

**理由**：
- Markdown 表格是人类可读的，也保留了列结构
- Embedding 模型能区分列标题和单元格内容
- LLM 生成阶段能利用表格结构做引用
- 相比 CSV/JSON，Markdown 在 chunk 中更紧凑

### Decision 3：集成位置——RobustPDFReader.load_data() 内

**选择**：在 `pypdf.PdfReader` 提取之前或之后，用 `pdfplumber` 单独打开同一 PDF 抽取表格。

流程变为：

```
RobustPDFReader.load_data()
  │
  ├─ ① pdfplumber.open(file_path) → 逐页 extract_tables()
  │   └─ {page_num: [table_as_markdown, ...]}
  │
  ├─ ② pypdf.PdfReader(file_path) → 逐页 text
  │
  ├─ ③ 合并：每页 text + "\n\n" + 该页的表格 Markdown
  │
  ├─ ④ 检测文本量 → 足够 → 逐页 Document
  │
  └─ ⑤ 不足 → _ocr_pdf() 兜底（pdfplumber 结果在此丢弃，
          因为扫描件没有表格可抽）
```

**理由**：
- pdfplumber 打开同一 PDF 文件是只读的，不影响 pypdf 或 OCR 提取
- 放在同一个函数内，避免跨函数传递状态
- 对 OCR 路径透明——pdfplumber 在扫描件上返回空表，自然跳过

### Decision 4：不做跨页表格合并

**选择**：第一版实现中，每个表格限制在单页内。跨页表格（如印章权限矩阵跨 2 页）作为两个独立表格处理。

**理由**：
- 跨页表格合并需要判断表头是否重复、是否同一表格的延续
- 复杂度显著增加，但收益不确定（检索时两页都会被召回，LLM 能自行关联）

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| pdfplumber 误将非表格文本识别为表格 | pdfplumber 的检测比较保守（依赖文本坐标对齐），误报率低；即使误报，Markdown 表格文本仍是有效语义 |
| 表格文本太长，撑爆 chunk 容量 | 一个页面内有多个大表时，Markdown 可能超过 512 token——但此情况罕见；如发生，SentenceSplitter 会自然切分 |
| pdfplumber 处理某些 PDF 崩溃 | 用 `try/except` 包裹，异常时静默跳过表格抽取，不影响全文提取 |
| 表格中有合并单元格 | pdfplumber 对简单合并单元格有基本支持，复杂合并会丢失结构——但总比无结构好 |

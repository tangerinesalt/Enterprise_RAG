## 1. Setup & Dependency

- [x] 1.1 Install `pdfplumber` package: `pip install pdfplumber`, add to requirements documentation

## 2. Implementation in indexer.py

- [x] 2.1 Add `_extract_tables_pdfplumber(file_path: str) -> dict[int, list[str]]` function

- [x] 2.2 Add a helper `_table_to_markdown(table: list[list[str]]) -> str`

- [x] 2.3 Modify `RobustPDFReader.load_data()`: after pypdf extraction, merge per-page table Markdown into the page text

- [x] 2.4 Wrap pdfplumber calls in `try/except` with log warning on failure

## 3. Verification

- [x] 3.1 Test on `考勤休假管理制度.pdf`: revision history table on page 2 extracted as Markdown — 118 pipes, proper `|---|` separators, column-aligned data ✓

- [x] 3.2 Test on `印章管理制度.pdf` (scanned): pdfplumber empty → OCR fallback used normally ✓

- [x] 3.3 Test on `PR&VO-HR01-2022002 员工福利管理制度.pdf` (scanned): same as 3.2 ✓

## 4. Re-index & Validate

- [x] 4.1 Re-index `管理制度` KB (考勤休假管理制度.pdf, 20.1s)
- [x] 4.2 Verify retrieval: "修订内容 人力资源部" returns table chunks with column data ✓; "迟到 扣绩效" returns 5/5 relevant, 4 with Markdown tables ✓
- [x] 4.3 Vector change: 242 → 262 (+20, from table Markdown expanding page text → more chunks per page)

## 1. Setup

- [x] 1.1 Install `rapid-table` package: `pip install rapid-table`（已验证可用，自动下载 slanet-plus.onnx 7.4MB）

## 2. Implementation in indexer.py

- [x] 2.1 Add `_html_table_to_markdown(html: str) -> str` helper function

- [x] 2.2 Add `_ocr_pdf_with_tables(file_path: str) -> list[str]` function

- [x] 2.3 RapidTable import guard with `try/except ImportError` → fallback to `_ocr_pdf_plain()`

- [x] 2.4 Add `ENABLE_TABLE_RECOGNITION = False` in `config/settings.py`

- [x] 2.5 Refactor `_ocr_pdf()` to dispatch: `ENABLE_TABLE_RECOGNITION` → `_ocr_pdf_with_tables()` or `_ocr_pdf_plain()`

## 3. Verification

- [x] 3.1 Test on `PGRZ-03` 印章管理制度.pdf: authority matrix page 4 → Markdown table with 160 pipes ✓
- [x] 3.2 Fallback: `_ocr_pdf_plain()` correctly processes scanned PDF without RapidTable ✓
- [x] 3.3 Import guard: RapidTable not installed → silent fallback via try/except ✓
- [x] 3.4 Performance: 13 pages in 27.8s (2.14s avg), plain text ~1.5s/page, table pages ~2.5s/page

## 4. Re-index & Validate

- [x] 4.1 Re-index PGRZ-03 with `ENABLE_TABLE_RECOGNITION=True`
- [x] 4.2 Retrieval: "审批权限 申请&中止" and "印章名称 使用人" return top-5 results ✓
- [x] 4.3 Vector count: 262 → 267 (+5, from structured table content)

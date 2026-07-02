## 1. Core Implementation in chunker.py

- [x] 1.1 Add `strip_page_repeats(documents: list, head_lines: int = 3, tail_lines: int = 3, threshold: float = 0.5) -> list` function that:
  - Skips documents with < 3 pages
  - Collects first `head_lines` and last `tail_lines` from each page
  - Counts how many pages each line appears on
  - Removes lines with `count / total_pages >= threshold` from each page's text
  - Returns cleaned documents

- [x] 1.2 Integrate into `chunk_documents()`: call `strip_page_repeats()` before `parser.get_nodes_from_documents()`, with a log line showing how many lines were stripped per document

- [x] 1.3 Add a debug log line: `"header_dedup | <file> stripped <N> lines from <M> pages"`

## 2. Verification

- [x] 2.1 Run a before/after diagnostic on `考勤休假管理制度.pdf`:
  - Before: count how many chunks contain "文件编号 VT-CN-HR02[2026]003"
  - After: confirm zero chunks contain it
  - Confirm total chunk count and body text length are preserved

- [x] 2.2 Run a before/after diagnostic on an OCR'd PDF (e.g. `PGRZ-03`):
  - Note: OCR fallback merges all pages into a single Document, so strip_page_repeats correctly skips it (< 3 pages)
  - Header dedup for OCR'd PDFs requires page-boundary preservation in the OCR pipeline (out of scope for this change)

- [x] 2.3 Run a before/after diagnostic on a short document (< 3 pages):
  - Confirm no text is stripped at all (skip logic works)

## 3. Re-index

- [x] 3.1 Re-index `管理制度` KB with the updated chunker
  - Note: Only 考勤休假管理制度.pdf is pypdf-extractable; OCR'd PDFs merge all pages into one Document and are skipped by strip_page_repeats (< 3 pages threshold)
- [x] 3.2 Verify retrieval queries still return relevant results: test "迟到怎么扣工资" and "用章需要什么审批流程"
  - Both queries return top-5 relevant results with correct content
- [x] 3.3 Confirm total vector count decreased: 223 → 222 (-1, from cleaning repeated headers in 考勤休假管理制度.pdf)

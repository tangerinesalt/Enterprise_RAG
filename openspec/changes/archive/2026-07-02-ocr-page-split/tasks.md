## 1. Implementation in indexer.py

- [x] 1.1 Modify `_ocr_pdf()` to return `list[str]` (one string per page) instead of merged `str`: collect OCR results per-page and return as a list

- [x] 1.2 Modify `RobustPDFReader.load_data()` OCR fallback path: iterate over `_ocr_pdf()` result list, create one `Document` per page with `page_label` `"ocr_p1"`, `"ocr_p2"`, etc.

## 2. Verification

- [x] 2.1 Run before/after diagnostic on a scanned PDF (e.g. `PGRZ05`): confirm page count goes from 1 Document → N Documents (one per page)

- [x] 2.2 Verify that `strip_page_repeats()` now applies to the OCR'd document: confirm header/footer patterns detected and stripped across the now-separate pages
  - 5 repeated header lines + 1 footer line detected → 0 remain after stripping ✓

- [x] 2.3 Confirm pypdf-extracted path is unaffected: run same diagnostic on `考勤休假管理制度.pdf` and verify pages still extracted correctly

## 3. Re-index

- [x] 3.1 Re-index `管理制度` KB with the updated OCR pipeline (14 files, 331s total)
- [x] 3.2 Verify vector count and retrieval quality: test "迟到怎么扣工资" and "用章需要什么审批流程" — both pass ✓
- [x] 3.3 Confirm vector change: 222 → 242 (+20, expected increase from per-page chunking)
  - OCR docs now get per-page Documents → more focused chunks + header dedup
  - strip_page_repeats confirmed working on OCR docs (PGRZ05: 5 header + 1 footer lines stripped) ✓

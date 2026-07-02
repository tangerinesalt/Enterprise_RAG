## 1. Implementation in chunker.py

- [x] 1.1 Add `_fix_orphan_table_fragments(nodes: list) -> list` function

- [x] 1.2 Integrate into `chunk_documents()` after SentenceSplitter

- [x] 1.3 Add INFO log: `"table_fix | fixed <N> orphan fragments across <M> nodes"`

## 2. Verification

- [x] 2.1 PGRZ-03 page 4: orphans 2 → 0 ✓
- [x] 2.2 Content integrity: fixed nodes start with `| header |\n|---|---|\n` ✓
- [x] 2.3 No-table document: 0 false positives ✓
- [x] 2.4 Unit test: orphan without preceding header left unchanged (correct) ✓

## 3. Re-index & Validate

- [x] 3.1 Re-index with updated chunker
- [x] 3.2 Retrieval: table results have correct headers; 0 orphan fragments in top-10 ✓
- [x] 3.3 Vector count: unchanged (337 → 337, only node text modified, not boundaries)

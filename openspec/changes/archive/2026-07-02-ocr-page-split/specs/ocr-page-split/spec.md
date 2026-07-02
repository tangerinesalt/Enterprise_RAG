## ADDED Requirements

### Requirement: OCR preserves page boundaries

The system SHALL return one Document per page when OCR is used as a fallback for scanned PDFs, matching the page-level behavior of pypdf-extracted documents.

#### Scenario: Multi-page scanned PDF produces per-page Documents
- **WHEN** processing a 6-page scanned PDF with no extractable text
- **THEN** the OCR fallback SHALL return exactly 6 Documents
- **THEN** each Document's metadata SHALL contain a `page_label` field

#### Scenario: OCR page labels are distinguishable
- **WHEN** OCR produces a Document for page N of a scanned PDF
- **THEN** its `page_label` SHALL follow the format `"ocr_p<N>"` (e.g., `"ocr_p1"`, `"ocr_p2"`)
- **THEN** this format SHALL be distinct from pypdf-extracted pages (`"p1"`, `"p2"`)

#### Scenario: Single-page scanned PDF
- **WHEN** processing a 1-page scanned PDF
- **THEN** the OCR fallback SHALL return a single Document with `page_label` `"ocr_p1"`

### Requirement: Empty OCR pages are preserved

The system SHALL preserve empty OCR pages in the Document list, matching the behavior of the pypdf extraction path.

#### Scenario: Blank page in scanned PDF
- **WHEN** a scanned PDF has a blank page (no text content after OCR)
- **THEN** the Document for that page SHALL have empty or whitespace-only text
- **THEN** the Document SHALL still be included in the returned list

#### Scenario: Downstream chunking filters empty pages
- **WHEN** the OCR path returns a Document with empty text
- **THEN** `chunk_documents()` SHALL process it normally (SentenceSplitter naturally produces no nodes from empty text)

### Requirement: OCR quality unchanged

The OCR recognition process SHALL NOT be modified—only the output structure changes from merged to per-page.

#### Scenario: Same OCR engine used
- **WHEN** OCR fallback is triggered
- **THEN** the same pypdfium2 + RapidOCR pipeline SHALL be used as before
- **THEN** the recognized text content per page SHALL be identical to what was previously embedded in the merged output

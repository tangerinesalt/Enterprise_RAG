## ADDED Requirements

### Requirement: RapidTable table recognition as optional fallback

The system SHALL provide an optional RapidTable-based table recognition path for scanned PDFs, activated when `rapid-table` is installed and configured.

#### Scenario: RapidTable available, table detected
- **WHEN** `rapid-table` is installed and a scanned PDF page contains a detectable table
- **THEN** the system SHALL use RapidTable's SLANet model to identify the table structure
- **THEN** the system SHALL extract the cell contents via the built-in RapidOCR engine
- **THEN** the system SHALL convert the HTML output to Markdown and merge it into the page's Document text

#### Scenario: RapidTable available, no table detected
- **WHEN** `rapid-table` is installed but a scanned PDF page has no table (plain text)
- **THEN** RapidTable SHALL return an empty result
- **THEN** the system SHALL fall back to RapidOCR for text recognition on that page

#### Scenario: RapidTable not installed
- **WHEN** `rapid-table` is not installed (`ImportError` on `rapid_table`)
- **THEN** the system SHALL silently fall back to the existing RapidOCR-only path
- **THEN** no error SHALL be raised

#### Scenario: RapidTable import failure
- **WHEN** RapidTable raises an exception during import (missing dependency, model download failure)
- **THEN** the system SHALL log the error at WARNING level
- **THEN** the system SHALL fall back to RapidOCR

### Requirement: Table format consistency

RapidTable-extracted tables SHALL be converted to Markdown format compatible with existing `pdf-table-extraction` output.

#### Scenario: Same Markdown format
- **WHEN** a table is extracted via RapidTable from a scanned PDF
- **THEN** its Markdown format SHALL be consistent with pdfplumber-extracted tables from `pdf-table-extraction`
- **THEN** both sources SHALL produce indistinguishable Markdown tables

### Requirement: Graceful performance degradation

The system SHALL handle the slower inference speed of RapidTable table recognition without blocking the indexing pipeline.

#### Scenario: Slow page skipped
- **WHEN** RapidTable processing on a single page exceeds a configurable timeout
- **THEN** the system SHALL fall back to RapidOCR for that page
- **THEN** the rest of the document SHALL continue processing

## MODIFIED Requirements

### Requirement: System SHALL parse uploaded documents using llama_index

#### Scenario: Parse a PDF with OCR fallback (modified)
- **WHEN** a .pdf file is uploaded and pypdf extracts insufficient text
- **THEN** `RobustPDFReader` falls back to OCR
- **THEN** if `rapid-table` is installed and table recognition is enabled, the page SHALL be analyzed for table content via RapidTable
- **THEN** detected tables SHALL be converted to Markdown and embedded in the page text

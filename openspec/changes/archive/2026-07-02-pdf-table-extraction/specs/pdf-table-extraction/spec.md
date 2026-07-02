## ADDED Requirements

### Requirement: Table detection with pdfplumber

The system SHALL use pdfplumber to detect and extract tables from pypdf-extractable PDF documents.

#### Scenario: Detect revision history table
- **WHEN** processing a PDF page that contains a revision history table with visible cell borders
- **THEN** pdfplumber SHALL detect the table and return its cell contents as a list of rows

#### Scenario: Detect borderless table
- **WHEN** processing a PDF page that contains a borderless table (text aligned in columns)
- **THEN** pdfplumber SHALL detect the table based on text coordinate alignment

#### Scenario: Scanned PDF with no text layer
- **WHEN** processing a scanned PDF page with no extractable text
- **THEN** pdfplumber SHALL return no tables
- **THEN** the existing OCR fallback SHALL still be used

#### Scenario: pdfplumber exception handling
- **WHEN** pdfplumber raises an exception during table extraction on a specific PDF
- **THEN** the system SHALL catch the exception, log a warning
- **THEN** the system SHALL continue with normal text extraction for that page

### Requirement: Table formatted as Markdown

Extracted tables SHALL be converted to Markdown format (`| col1 | col2 |`) and embedded into the page's Document text.

#### Scenario: Table to Markdown conversion
- **WHEN** a table with header row and 3 data rows is extracted from a page
- **THEN** the output SHALL contain a Markdown table with header separator line and all data rows
- **THEN** column alignment SHALL be left-aligned

#### Scenario: Empty table rows skipped
- **WHEN** pdfplumber returns a table row where all cells are empty or whitespace
- **THEN** that row SHALL NOT appear in the Markdown output

### Requirement: Table merged with page text

The Markdown table SHALL be appended to the page's extracted text, separated by two newlines, preserving the page-level Document structure.

#### Scenario: Page with text and one table
- **WHEN** a page has both body text and a detectable table
- **THEN** the Document text SHALL contain the body text followed by a blank line and the Markdown table

#### Scenario: Page with multiple tables
- **WHEN** a page has 2 or more detectable tables
- **THEN** each table SHALL appear as a separate Markdown table, separated by blank lines

### Requirement: Table data retrievable via search

The Markdown table content SHALL be indexed and retrievable through the existing search pipeline.

#### Scenario: Cell value matches query
- **WHEN** a user queries for a term that appears in a table cell (e.g., "人力资源部")
- **THEN** the chunk containing that Markdown table SHALL be returned as a search result

#### Scenario: Column header in query
- **WHEN** a user queries for a column-related term (e.g., "修订内容")
- **THEN** chunks containing tables with that header SHALL be returned

## MODIFIED Requirements

### Requirement: System SHALL parse uploaded documents using llama_index

(The existing requirement from kb-ingestion spec. Added below is the table extraction step.)

#### Scenario: PDF with table content
- **WHEN** a PDF with structured table content is indexed
- **THEN** `RobustPDFReader` SHALL extract tables via pdfplumber before falling back to pypdf text extraction
- **THEN** table content SHALL be merged into the page text as Markdown before chunking

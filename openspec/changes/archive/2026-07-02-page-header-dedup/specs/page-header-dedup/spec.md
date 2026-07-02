## ADDED Requirements

### Requirement: Detect cross-page repeated text

The system SHALL analyze all pages of a multi-page document and identify text lines that appear in the same position (first N lines or last N lines) on more than 50% of pages.

#### Scenario: Header detection on 11-page document
- **WHEN** processing an 11-page PDF where the first 2 lines of every page contain the same file number and version string
- **THEN** the system SHALL identify those 2 lines as repeated headers

#### Scenario: Footer detection on 11-page document
- **WHEN** processing an 11-page PDF where the last line of every page contains a page number pattern
- **THEN** the system SHALL identify that line as a repeated footer

#### Scenario: Single-page document skip
- **WHEN** processing a document with fewer than 3 pages
- **THEN** the system SHALL skip the header/footer detection

#### Scenario: No repeated text
- **WHEN** processing a document where no text line appears on more than 50% of pages in the same position
- **THEN** the system SHALL not modify any page text

### Requirement: Strip repeated text before chunking

The system SHALL remove detected repeated headers and footers from each page's text before passing to SentenceSplitter.

#### Scenario: Header stripped from all chunks
- **WHEN** a 5-line header is detected across all pages of a 10-page document
- **THEN** none of the resulting chunks SHALL contain those 5 lines

#### Scenario: Only matching lines removed
- **WHEN** a 2-line header is detected but a 3rd varying line at the top of each page is not
- **THEN** only the 2 matching lines SHALL be removed, the 3rd line SHALL be preserved

### Requirement: Preserve remaining document structure

The system SHALL preserve all non-repeated content, including document structure, paragraph breaks, and semantic ordering.

#### Scenario: Body text unchanged
- **WHEN** processing a document with headers stripped
- **THEN** the body text between header and footer SHALL remain unchanged

#### Scenario: Multi-paragraph content preserved
- **WHEN** a document has headers removed
- **THEN** SentenceSplitter SHALL still receive the complete body text with all paragraph separators intact

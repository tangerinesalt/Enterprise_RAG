## ADDED Requirements

### Requirement: Metadata-based page filtering
The retrieval system SHALL filter out known boilerplate pages (cover, foreword, table of contents, drafter lists) using `MetadataFilters` before passing results to the LLM.

#### Scenario: Cover page excluded
- **WHEN** a user sends a query
- **THEN** chunks with `page_label="p1"` SHALL be excluded from retrieval results

#### Scenario: Foreword page excluded
- **WHEN** a user sends a query
- **THEN** chunks with `page_label="p5"` SHALL be excluded from retrieval results

#### Scenario: OCR fallback page excluded
- **WHEN** a user sends a query
- **THEN** chunks with `page_label="ocr"` SHALL be excluded from retrieval results

### Requirement: Score threshold filtering
The retrieval system SHALL discard retrieved nodes with a relevance score below a configurable threshold, preventing unrelated chunks from reaching the LLM.

#### Scenario: Low-score chunks discarded
- **WHEN** retrieval returns nodes with scores below 0.6
- **THEN** those nodes SHALL NOT be passed to the LLM for answer generation

#### Scenario: All chunks below threshold
- **WHEN** all retrieved nodes have scores below 0.6
- **THEN** the system SHALL return a message indicating no relevant information was found

### Requirement: Shared retriever between chat and chat_stream
Both `chat()` and `chat_stream()` SHALL use the same retriever instance for consistent retrieval behavior.

#### Scenario: Synchronous chat uses filtered retriever
- **WHEN** a user sends a message via the synchronous `chat()` endpoint
- **THEN** the retrieval SHALL apply the same MetadataFilters and score threshold as the streaming endpoint

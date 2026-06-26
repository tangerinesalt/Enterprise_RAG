## ADDED Requirements

### Requirement: Custom NodeParser with enterprise chunking parameters
The indexing system SHALL use a custom `SentenceSplitter` with configurable chunk size, overlap, and paragraph separator instead of LlamaIndex defaults.

#### Scenario: Configurable chunk size
- **WHEN** the indexer processes documents
- **THEN** it SHALL use `chunk_size=512` (or the value configured in `config/settings.py`)
- **THEN** it SHALL use `chunk_overlap=128` (or the value configured in `config/settings.py`)
- **THEN** it SHALL use `paragraph_separator="\n\n"` (or the value configured in `config/settings.py`)

#### Scenario: Nodes instead of documents
- **WHEN** building the vector index
- **THEN** the system SHALL use `VectorStoreIndex(nodes=nodes, ...)` instead of `VectorStoreIndex.from_documents(documents, ...)`
- **THEN** the nodes SHALL be produced by `SentenceSplitter.get_nodes_from_documents()`

### Requirement: Page type metadata detection
Each node SHALL have a `page_type` metadata field automatically detected from the source document's page number and content.

#### Scenario: Page type classification
- **WHEN** a document is processed
- **THEN** the system SHALL classify each page using heuristic rules:
  - `page_label="p1"` → `page_type="cover"`
  - `page_label` in `["p2", "p3", "p4"]` → `page_type="toc"`
  - `page_label="p5"` and text contains "前言" → `page_type="foreword"`
  - `page_label` starts with "ocr" → `page_type="ocr_scanned"`
  - Otherwise → `page_type="content"`

#### Scenario: Node metadata enrichment
- **WHEN** a node is created from a page
- **THEN** its metadata SHALL include: `page_type`, `page_label`, `file_path`, `chunk_index`, `total_chunks`

### Requirement: Configurable chunking parameters
Chunking parameters SHALL be configurable in `config/settings.py` and readable at index time.

#### Scenario: Settings integration
- **WHEN** the indexer starts
- **THEN** it SHALL read `CHUNK_SIZE`, `CHUNK_OVERLAP`, `CHUNK_PARAGRAPH_SEPARATOR` from settings
- **THEN** the `SentenceSplitter` SHALL be initialized with these values

### Requirement: Retriever uses page_type filters
The `build_retriever()` function SHALL filter nodes by `page_type` instead of hardcoded `page_label` values.

#### Scenario: Page type filtering
- **WHEN** a query is executed
- **THEN** the MetadataFilters SHALL exclude nodes with `page_type` in `["cover", "toc", "foreword", "ocr_scanned"]`
- **THEN** nodes with `page_type="content"` SHALL be the only ones considered for retrieval

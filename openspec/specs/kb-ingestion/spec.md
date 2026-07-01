## ADDED Requirements

### Requirement: System SHALL parse uploaded documents using llama_index

The system SHALL use `SimpleDirectoryReader` and `RobustPDFReader` to extract text from uploaded documents.

#### Scenario: Parse a text file
- **WHEN** a .txt file is uploaded to a knowledge base
- **THEN** `SimpleDirectoryReader` reads it as UTF-8 text
- **THEN** text content is returned for chunking

#### Scenario: BOM character SHALL be stripped
- **WHEN** a .txt source file contains `﻿` (UTF-8 BOM) at position 0
- **THEN** the BOM is stripped during chunking via `chunk_documents()`
- **THEN** the vector stored in ChromaDB does NOT contain `﻿`
- **THEN** the source text displayed in chat does NOT contain `﻿`

#### Scenario: PDF text extraction with BOM
- **WHEN** a PDF page extracts text that contains BOM
- **THEN** the BOM is stripped during chunking
- **THEN** no downstream data contains BOM

#### Scenario: Parse a PDF with OCR fallback
- **WHEN** a .pdf file is uploaded and pypdf extracts insufficient text
- **THEN** `RobustPDFReader` falls back to `rapidocr-onnxruntime` + `pypdfium2`

### Requirement: System SHALL chunk and embed documents

The system SHALL split document text into chunks and convert each chunk to a vector using Ollama Embedding.

#### Scenario: Default chunking
- **WHEN** a document is indexed
- **THEN** text is split into chunks of configurable size (default 1024 tokens)
- **THEN** each chunk is embedded via Ollama `/api/embed` using `qwen3-embedding:4b`
- **THEN** each chunk's metadata includes `file_name` and `page_label`

### Requirement: System SHALL store vectors in per-knowledge-base ChromaDB

Each knowledge base SHALL have its own independent ChromaDB instance at `kb/<name>/vector_db/`.

#### Scenario: Independent vector stores
- **WHEN** documents are indexed into knowledge base "A"
- **THEN** vectors are stored in `kb/A/vector_db/`
- **WHEN** documents are indexed into knowledge base "B"
- **THEN** vectors are stored in `kb/B/vector_db/`
- **THEN** querying "A" does not return results from "B"

## MODIFIED Requirements

### Requirement: Index SHALL persist nodes for BM25

The indexing process SHALL save the chunked nodes list alongside the vector store so BM25 can use the same texts.

#### Scenario: Nodes saved during indexing
- **WHEN** `index_file` completes chunking and vector storage
- **THEN** the chunked nodes list is saved to a per-knowledge-base cache (e.g., pickle)
- **THEN** `_build_bm25_retriever` reads from this cache instead of source files

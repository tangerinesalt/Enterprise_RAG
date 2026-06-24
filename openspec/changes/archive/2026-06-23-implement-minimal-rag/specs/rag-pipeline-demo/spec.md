## ADDED Requirements

### Requirement: parse_index.py SHALL parse documents and build vector index

The script SHALL read a document file, extract text, split into chunks, compute embeddings via Ollama, and store in ChromaDB.

#### Scenario: Index a .txt file
- **WHEN** user runs `python parse_index.py sample.txt`
- **THEN** the file is read as UTF-8 text
- **THEN** text is split into chunks of ~500 chars with 50-char overlap
- **THEN** each chunk is sent to Ollama Embedding API
- **THEN** chunks + vectors are stored in ChromaDB at `rag_demo_db/`
- **THEN** script prints: file name, chunk count, vector dimension, completion message

#### Scenario: Index a PDF file
- **WHEN** user runs `python parse_index.py document.pdf`
- **THEN** text is extracted from all PDF pages using pypdf
- **THEN** extracted text follows the same chunk → embed → store flow

#### Scenario: Index an unsupported file
- **WHEN** user runs `python parse_index.py image.png`
- **THEN** script prints "Unsupported file format: .png" and exits

### Requirement: retrieve_generate.py SHALL answer questions using RAG

The script SHALL accept a query, retrieve relevant chunks from ChromaDB, and generate an answer via Ollama LLM.

#### Scenario: Query with indexed documents
- **WHEN** user runs `python retrieve_generate.py "what is this about?"`
- **THEN** the query is embedded using the same Ollama model
- **THEN** top-5 similar chunks are retrieved from ChromaDB
- **THEN** retrieved chunks are printed as "Retrieved sources"
- **THEN** a RAG prompt is constructed with context + question
- **THEN** Ollama LLM generates an answer
- **THEN** answer is printed, followed by source snippets

#### Scenario: Query without indexed documents
- **WHEN** user runs `python retrieve_generate.py "question"` and no index exists
- **THEN** script prints "No index found. Run parse_index.py first." and exits

### Requirement: README SHALL explain how to run the demo

The README SHALL provide step-by-step instructions to run both scripts.

#### Scenario: README content
- **WHEN** user reads `example/README.md`
- **THEN** it contains: prerequisites (Python packages), step 1 (parse_index.py), step 2 (retrieve_generate.py), expected output format

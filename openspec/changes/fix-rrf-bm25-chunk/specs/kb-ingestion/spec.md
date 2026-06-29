## MODIFIED Requirements

### Requirement: BM25 index SHALL be built independently from vector index

The BM25 retriever SHALL build its index from raw source file paragraphs, separate from the SentenceSplitter chunking used for vector indexing.

#### Scenario: BM25 reads source files directly
- **WHEN** BM25 index is constructed
- **THEN** it reads `.txt` files from the KB's `files/` directory
- **THEN** it splits text by `\n\n` to get paragraph-level units
- **THEN** it builds its own tokenized corpus independent of vector index chunks

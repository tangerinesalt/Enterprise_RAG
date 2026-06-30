## MODIFIED Requirements

### Requirement: Index SHALL persist nodes for BM25

The indexing process SHALL save the chunked nodes list alongside the vector store so BM25 can use the same texts.

#### Scenario: Nodes saved during indexing
- **WHEN** `index_file` completes chunking and vector storage
- **THEN** the chunked nodes list is saved to a per-knowledge-base cache (e.g., pickle)
- **THEN** `_build_bm25_retriever` reads from this cache instead of source files

## ADDED Requirements

### Requirement: BM25 index SHALL use original paragraph boundaries

The BM25 retriever SHALL index text at original `\n\n` paragraph boundaries from source files, not from SentenceSplitter-merged chunks.

#### Scenario: BM25 indexes raw paragraphs
- **WHEN** a knowledge base contains a file with paragraphs separated by `\n\n`
- **THEN** BM25 treats each `\n\n`-delimited section as an independent indexing unit
- **THEN** the paragraph count equals the number of `\n\n` sections across all files

#### Scenario: Paragraph-level BM25 outperforms chunk-level BM25
- **WHEN** user queries "什么是数字化开户"
- **THEN** the paragraph-level BM25 ranks the D2 paragraph (数字化开户) at #1 or close to #1
- **THEN** the ranking is strictly better than the chunk-level BM25 for the same query

### Requirement: BM25 index SHALL build from source files

The BM25 retriever SHALL build its index directly from the knowledge base's source files, not from the vector index's docstore.

#### Scenario: Independent BM25 index rebuild
- **WHEN** `build_retriever` is called with a kb_name
- **THEN** BM25 reads `.txt` files from `kb/<name>/files/` recursively
- **THEN** each file is split by `\n\n` into paragraphs
- **THEN** the BM25 index is cached by kb_name

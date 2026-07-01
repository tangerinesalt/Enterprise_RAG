## ADDED Requirements

### Requirement: BM25 SHALL use vector chunk texts

BM25 SHALL index the same TextNode texts as the vector index, enabling node_id-level RRF fusion.

#### Scenario: BM25 built from vector nodes
- **WHEN** `_build_bm25_retriever` is called
- **THEN** it receives the same TextNode list used by VectorStoreIndex
- **THEN** each BM25 node has the same node_id as its vector counterpart
- **THEN** RRF fusion can deduplicate by node_id and apply dual-path scoring

#### Scenario: BM25 matches vector recall for known queries
- **WHEN** a query matches a known paragraph (e.g., "数字化开户")
- **THEN** BM25 on chunk texts ranks the correct chunk similarly to the vector method
- **THEN** RRF fusion rewards the node appearing in both result sets

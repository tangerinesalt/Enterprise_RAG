## ADDED Requirements

### Requirement: BM25 keyword retrieval
The system SHALL provide BM25 keyword-based retrieval as a complement to vector similarity search, using jieba for Chinese text tokenization.

#### Scenario: BM25 returns keyword-matched results
- **WHEN** a user query contains exact technical terms (e.g., "GB/T 47739", "硅材料")
- **THEN** chunks containing those exact terms SHALL receive higher BM25 scores

#### Scenario: BM25 index built from nodes
- **WHEN** a chat session starts with a bound knowledge base
- **THEN** the system SHALL build a BM25 index from the KB's ChromaDB nodes on first retrieval

#### Scenario: BM25 index rebuild
- **WHEN** the knowledge base is reindexed
- **THEN** the BM25 index SHALL be rebuilt lazily on next retrieval

### Requirement: RRF fusion
The system SHALL combine vector and BM25 retrieval results using Reciprocal Rank Fusion (RRF) to produce a unified ranked list.

#### Scenario: Vector and BM25 results merged
- **WHEN** both retrievers return results for a query
- **THEN** the system SHALL compute RRF scores using `score(d) = 1/(k + rank_v(d)) + 1/(k + rank_b(d))` with `k=60`
- **THEN** the top-5 results by RRF score SHALL be returned to the LLM

#### Scenario: Only one retriever has results
- **WHEN** either vector or BM25 retriever returns no results
- **THEN** the system SHALL fall back to the non-empty retriever's results

### Requirement: Chinese tokenization
The BM25 retriever SHALL use jieba for Chinese word segmentation to handle the photovoltaic domain vocabulary correctly.

#### Scenario: Chinese terms tokenized
- **WHEN** a Chinese query is processed by BM25
- **THEN** jieba SHALL segment the query into meaningful tokens (e.g., "光伏电池材料" → ["光伏", "电池", "材料"])

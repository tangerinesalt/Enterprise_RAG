## MODIFIED Requirements

### Requirement: RRF fusion SHALL use node_id-level dedup

With shared chunk texts, RRF fusion's node_id dedup SHALL correctly identify common results from both retrieval paths.

#### Scenario: Dual-path bonus for shared chunks
- **WHEN** a chunk appears in both vector results and BM25 results
- **THEN** RRF identifies it by matching node_id
- **THEN** the chunk receives RRF scores from both paths (vector_weight + bm25_weight)
- **THEN** the chunk appears once in the fused list (dedup), with the combined score

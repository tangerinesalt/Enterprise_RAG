## MODIFIED Requirements

### Requirement: RRF fusion SHALL support weighted scoring

The RRF fusion function SHALL accept vector_weight and bm25_weight parameters instead of equal weighting.

#### Scenario: Weighted RRF with defaults
- **WHEN** `_rrf_fusion` is called with default parameters
- **THEN** vector results contribute `0.7 * 1/(k+rank+1)` to the fusion score
- **THEN** BM25 results contribute `0.3 * 1/(k+rank+1)` to the fusion score
- **THEN** the fused ranking reflects the weighted combination

#### Scenario: Weighted RRF preserves vector ranking for good queries
- **WHEN** vector search ranks correct answer at #1 and BM25 ranks it at #8
- **THEN** the weighted RRF rank is closer to #1 than to #8
- **THEN** the ranking is strictly better than equal-weight RRF

### Requirement: Retrieval mode SHALL be configurable

The system SHALL support both hybrid (vector+BM25+RRF) and vector-only retrieval modes.

#### Scenario: Hybrid mode (default)
- **WHEN** `build_retriever` is called with `mode='hybrid'`
- **THEN** both vector and BM25 retrievers are built
- **THEN** results are combined via weighted RRF fusion
- **THEN** the reranker is applied on fused results

#### Scenario: Vector-only mode
- **WHEN** `build_retriever` is called with `mode='vector-only'`
- **THEN** only the VectorIndexRetriever (with threshold filter) is built
- **THEN** no BM25 retriever or RRF fusion is used
- **THEN** the reranker is applied directly on vector results

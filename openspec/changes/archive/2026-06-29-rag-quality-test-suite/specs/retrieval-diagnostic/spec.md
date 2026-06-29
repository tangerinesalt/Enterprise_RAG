## ADDED Requirements

### Requirement: Diagnostic SHALL trace retrieval pipeline stage by stage

The diagnostic script SHALL execute and report each stage of the retrieval pipeline independently, showing how rankings and scores change at each step.

#### Scenario: Run diagnostic with custom query
- **WHEN** user runs `python test/test_retrieval_diagnostic.py 062500 "A1是什么"`
- **THEN** output shows Stage 1 (ChromaDB cosine_sim ranking)
- **THEN** output shows Stage 2 (VectorIndexRetriever + threshold filtering)
- **THEN** output shows Stage 3 (BM25 retrieval with jieba tokenization)
- **THEN** output shows Stage 4 (RRF fusion) with source tracking (vec#N / bm25#N)
- **THEN** output shows Stage 5 (Reranker final ranking with scores)
- **THEN** each stage shows which entries match the query keywords

### Requirement: Diagnostic SHALL auto-detect anomalies

The script SHALL check for known failure patterns and emit structured warnings.

#### Scenario: Full-negative cosine similarity
- **WHEN** all ChromaDB results have cosine_sim < 0
- **THEN** diagnostic prints `[E01] All cosine_sim values are negative — embedding model may be incompatible with this query domain`

#### Scenario: High threshold filter rate
- **WHEN** more than 50% of VectorIndexRetriever results are filtered by the threshold
- **THEN** diagnostic prints `[E02] Threshold filtering {X}% of results — threshold may be too high`

#### Scenario: ChromaDB duplicates detected
- **WHEN** duplicate text entries are found in ChromaDB results
- **THEN** diagnostic prints `[E03] Duplicate rate: {X}% — index is not idempotent`

### Requirement: Diagnostic SHALL output JSON report

The script SHALL write a structured JSON report for comparison across runs.

#### Scenario: JSON output file
- **WHEN** user runs `python test/test_retrieval_diagnostic.py 062500 "A1是什么"`
- **THEN** a JSON file is written to `test/diagnostic_output/062500_<timestamp>.json`
- **THEN** the JSON contains all stage results, anomaly flags, and run config

### Requirement: Diagnostic SHALL accept CLI parameters

The script SHALL support configurable parameters via CLI.

#### Scenario: Custom top_k and top_n
- **WHEN** user runs `python test/test_retrieval_diagnostic.py 062500 "A1是什么" --top-k 16 --top-n 8 --threshold 0.1`
- **THEN** the pipeline uses top_k=16, top_n=8, threshold=0.1
- **THEN** output reflects the custom configuration

#### Scenario: Show help
- **WHEN** user runs `python test/test_retrieval_diagnostic.py --help`
- **THEN** usage text shows all parameters with defaults

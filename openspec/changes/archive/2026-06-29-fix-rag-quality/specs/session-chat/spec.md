## MODIFIED Requirements

### Requirement: Vector score threshold SHALL be lowered

The `_ScoreThresholdRetriever` threshold SHALL be reduced from 0.6 to 0.2 to match the current embedding model's score distribution.

#### Scenario: Vector results pass threshold
- **WHEN** a query returns vector results with cosine similarity scores above 0.2
- **THEN** those results are NOT filtered out by the threshold
- **THEN** they reach the RRF fusion stage and participate in hybrid retrieval

#### Scenario: Embedding scores are low
- **WHEN** the embedding model yields maximum score < 0.5 for a query
- **THEN** results are still passed through (not blocked by threshold)
- **THEN** RRF fusion and reranker are the primary quality gate

### Requirement: Source text SHALL NOT be truncated

The source text returned to the LLM SHALL contain the full chunk content, not a 300-character prefix.

#### Scenario: Full chunk text in sources
- **WHEN** a source node has 512 characters of text
- **THEN** the source response contains all 512 characters
- **THEN** no `[:300]` truncation is applied

#### Scenario: Streaming chat also returns full text
- **WHEN** streaming chat (`chat_stream`) returns sources
- **THEN** the source text is the complete chunk text, not truncated

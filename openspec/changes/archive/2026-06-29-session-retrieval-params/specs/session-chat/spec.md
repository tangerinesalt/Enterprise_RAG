## MODIFIED Requirements

### Requirement: System SHALL retrieve with session-level top_k

The system SHALL apply the session's `top_k` value to vector retrieval, BM25 retrieval, and RRF fusion.

#### Scenario: Chat uses session top_k
- **WHEN** user runs `session chat my-session "问题"` and config has `top_k: 10`
- **THEN** `VectorIndexRetriever(similarity_top_k=10)` is used
- **THEN** `BM25Retriever(similarity_top_k=10)` is used
- **THEN** `_rrf_fusion` returns the top 10 fused results

#### Scenario: Chat uses session top_n
- **WHEN** user runs `session chat my-session "问题"` and config has `top_n: 7`
- **THEN** `SentenceTransformerRerank(top_n=7)` is used as node postprocessor

#### Scenario: Stream chat also respects params
- **WHEN** user sends `POST /api/session/chat/stream` with session config `top_k=12, top_n=5`
- **THEN** the same parameter propagation applies as in non-stream chat

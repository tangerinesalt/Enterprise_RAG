## Purpose

Define requirements for session chat persistence, retrieval, and answer generation, covering both CLI and streaming interfaces.
## Requirements
### Requirement: System SHALL persist chat history via SimpleChatStore

The system SHALL persist each conversation to a specific chat file via `SimpleChatStore`. When a request provides `chat_file`, the system SHALL load and append to that exact file instead of inferring the target from a session-global current chat.

#### Scenario: Chat file creates per session
- **WHEN** user runs `session chat my-session "question"` for the first time without specifying `chat_file`
- **THEN** a new chat file is created at `sessions/my-session/chats/<timestamp>.json`
- **THEN** the file contains the user message and assistant response

#### Scenario: Chat continues on explicit chat file
- **WHEN** client sends `POST /api/session/chat` with `{"name": "my-session", "query": "follow-up", "chat_file": "2026_07_06_10_00.json"}`
- **THEN** the existing `SimpleChatStore` is loaded from `2026_07_06_10_00.json`
- **THEN** the new messages are appended to that same file
- **THEN** the assistant response uses that file's prior conversation context

#### Scenario: Explicit chat file ignores unrelated active chat metadata
- **WHEN** session metadata `active_chat` is `chat-b.json`
- **AND** client sends a request with `chat_file: "chat-a.json"`
- **THEN** the system appends the conversation to `chat-a.json`
- **THEN** it does NOT switch to `chat-b.json` because of session-global metadata

### Requirement: System SHALL retrieve and generate answers

The system SHALL retrieve relevant chunks from the bound knowledge base and generate an answer via LLM.

#### Scenario: Chat with bound KB
- **WHEN** user runs `python -m app.modules.kb_manager.cli session chat my-session "什么是A1？"`
- **THEN** the session's bound KB is loaded from `config.json`
- **THEN** ChromaDB vectors are queried for top-5 relevant chunks
- **THEN** the answer is generated via Ollama LLM
- **THEN** the answer is printed to console
- **THEN** source citations are printed

#### Scenario: Chat without bound KB
- **WHEN** user runs `session chat my-session "question"` and no KB is bound
- **THEN** system prints "No knowledge base bound to session 'my-session'"

### Requirement: Frontend SHALL not auto-select chat on session page load

The frontend SHALL NOT automatically select or load any chat file when the user enters a session page. Chat files are loaded only on explicit user action (clicking a chat in the sidebar).

#### Scenario: No chat auto-selected on entry
- **WHEN** user navigates to `/session/<name>` via web UI
- **THEN** the session info and chat list are loaded from the server
- **THEN** no chat file content is fetched
- **THEN** no chat file is shown in the main content area

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

### Requirement: RRF fusion SHALL use weighted scoring

The RRF fusion SHALL apply vector_weight=0.7 and bm25_weight=0.3 instead of equal weighting.

#### Scenario: Weighted RRF preserves vector ranking
- **WHEN** vector search ranks correct answer at #3 and BM25 ranks it at #10
- **THEN** weighted RRF rank is #3 (unchanged from vector), not degraded
- **THEN** the RRF score spread is at least 5x wider than equal-weight RRF

### Requirement: RRF fusion SHALL use node_id-level dedup

With shared chunk texts, RRF fusion's node_id dedup SHALL correctly identify common results from both retrieval paths.

#### Scenario: Dual-path bonus for shared chunks
- **WHEN** a chunk appears in both vector results and BM25 results
- **THEN** RRF identifies it by matching node_id
- **THEN** the chunk receives RRF scores from both paths (vector_weight + bm25_weight)
- **THEN** the chunk appears once in the fused list (dedup), with the combined score

### Requirement: Retrieval mode SHALL support vector-only

The session config SHALL support `retriever_mode` field: `"hybrid"` (default) or `"vector-only"`.

#### Scenario: Vector-only mode
- **WHEN** session config has `"retriever_mode": "vector-only"`
- **THEN** `build_retriever` skips BM25 construction and RRF fusion
- **THEN** only VectorIndexRetriever (with threshold filter) is used
- **THEN** the reranker is applied directly on vector results


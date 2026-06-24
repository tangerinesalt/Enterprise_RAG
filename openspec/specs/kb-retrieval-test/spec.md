## ADDED Requirements

### Requirement: Test script SHALL query a knowledge base

The system SHALL provide a simple test script `test/test_retrieve.py` to verify knowledge base functionality.

#### Scenario: Query by knowledge base name
- **WHEN** user runs `python test/test_retrieve.py my-docs "what is this about?"`
- **THEN** the script loads ChromaDB from `kb/my-docs/vector_db/`
- **THEN** retrieves top-5 relevant chunks
- **THEN** generates an answer using Ollama LLM
- **THEN** prints the answer with source citations

#### Scenario: Query non-existent knowledge base
- **WHEN** user runs `python test/test_retrieve.py unknown-kb "question"`
- **THEN** system prints "Knowledge base 'unknown-kb' not found"
- **THEN** exits with non-zero code

#### Scenario: Query empty knowledge base
- **WHEN** user runs `python test/test_retrieve.py empty-kb "question"`
- **THEN** system prints "No documents indexed in 'empty-kb'"

### Requirement: Test script SHALL be easy to remove

The test script SHALL be placed in `test/` directory to be clearly identifiable as test code.

#### Scenario: File location
- **WHEN** the change is archived
- **THEN** `test/test_retrieve.py` is explicitly mentioned for deletion
- **THEN** the `test/` directory is removed

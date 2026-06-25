## ADDED Requirements

### Requirement: System SHALL persist chat history via SimpleChatStore

The system SHALL use LlamaIndex's `SimpleChatStore` to manage chat messages, persisting to JSON files.

#### Scenario: Chat file creates per session
- **WHEN** user runs `session chat my-session "question"` for the first time
- **THEN** a chat file is created at `sessions/my-session/chats/<timestamp>.json`
- **THEN** the file name follows the format `年_月_日_时_分.json`
- **THEN** the file contains the user message and assistant response

#### Scenario: Chat file naming with conflict
- **WHEN** two chat sessions start in the same minute
- **THEN** the second file gets suffix `_1`, third gets `_2`, etc.

#### Scenario: Multi-turn conversation
- **WHEN** user runs `session chat my-session "follow-up"` on an existing chat file
- **THEN** the existing SimpleChatStore is loaded from the most recent chat file
- **THEN** the new messages are appended to the same file
- **THEN** the assistant's response considers previous conversation context

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

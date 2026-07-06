## MODIFIED Requirements

### Requirement: System SHALL persist chat history via SimpleChatStore

The system SHALL use LlamaIndex's `SimpleChatStore` to manage chat messages, persisting to JSON files for both synchronous and streaming chat flows.

#### Scenario: Chat file creates per session
- **WHEN** user runs `session chat my-session "question"` for the first time
- **THEN** a chat file is created at `sessions/my-session/chats/<timestamp>.json`
- **THEN** the file name follows the format `骞確鏈坃鏃鏃禵鍒?json`
- **THEN** the file contains the user message and assistant response

#### Scenario: Chat file naming with conflict
- **WHEN** two chat sessions start in the same minute
- **THEN** the second file gets suffix `_1`, third gets `_2`, etc.

#### Scenario: Multi-turn conversation
- **WHEN** user runs `session chat my-session "follow-up"` on an existing chat file
- **THEN** the existing SimpleChatStore is loaded from the most recent chat file
- **THEN** the new messages are appended to the same file
- **THEN** the assistant's response considers previous conversation context

#### Scenario: Synchronous chat preserves first question on failure
- **WHEN** the system has already determined the target chat file for a synchronous chat request and a later KB, storage, retrieval, or model step fails
- **THEN** the user message is already persisted in the chat file
- **THEN** an assistant error message is appended to the same chat file
- **THEN** the chat file is not left as an empty shell

#### Scenario: Streaming chat preserves first question on failure
- **WHEN** the system has already determined the target chat file for a streaming chat request and a later KB, storage, retrieval, or model step fails
- **THEN** the user message is already persisted in the chat file
- **THEN** an assistant error message is appended to the same chat file
- **THEN** reopening the chat shows the failed turn instead of an empty conversation

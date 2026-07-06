## ADDED Requirements

### Requirement: Session SHALL treat active_chat as recent-selection metadata

The system SHALL store `active_chat` as best-effort recent-selection metadata, not as the authoritative current chat for every page or user in the same session.

#### Scenario: Selecting a chat updates metadata
- **WHEN** a client selects `chat-a.json` in session `my-session`
- **THEN** the session metadata MAY update `active_chat` to `chat-a.json`
- **THEN** the field records recent selection state for compatibility purposes

#### Scenario: Two pages select different chats
- **WHEN** page A selects `chat-a.json`
- **AND** page B later selects `chat-b.json`
- **THEN** the later metadata value MAY become `chat-b.json`
- **THEN** page A is NOT required to abandon its own selected chat
- **THEN** the session model does NOT assume one shared authoritative current chat across all pages

#### Scenario: Explicit chat request does not require active_chat sync
- **WHEN** a client already knows the target `chat_file`
- **THEN** the client can continue chatting on that file without first making `active_chat` match it

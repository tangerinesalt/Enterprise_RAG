## ADDED Requirements

### Requirement: User SHALL create a knowledge base by name

The system SHALL create a new knowledge base directory with initialized file storage and vector database.

#### Scenario: Create a new knowledge base
- **WHEN** user runs `python -m app.kb_manager.cli kb create my-docs`
- **THEN** directory `kb/my-docs/` is created
- **THEN** subdirectory `kb/my-docs/files/` is created
- **THEN** subdirectory `kb/my-docs/vector_db/` is created
- **THEN** system prints "Knowledge base 'my-docs' created"

#### Scenario: Create duplicate knowledge base
- **WHEN** user runs `kb create my-docs` and `kb/my-docs/` already exists
- **THEN** system prints "Knowledge base 'my-docs' already exists"
- **THEN** no directories are modified

### Requirement: User SHALL upload a file to a knowledge base

The system SHALL copy a file into the knowledge base's file storage, parse it, chunk it, embed it, and index it in the vector database.

#### Scenario: Upload a new file
- **WHEN** user runs `python -m app.kb_manager.cli kb upload my-docs /path/to/report.pdf`
- **THEN** the file is copied to `kb/my-docs/files/report.pdf`
- **THEN** the file is parsed and its text is chunked
- **THEN** chunks are embedded and stored in `kb/my-docs/vector_db/`
- **THEN** system prints the number of chunks indexed

#### Scenario: Upload file to non-existent knowledge base
- **WHEN** user runs `kb upload unknown-kb file.pdf` and the knowledge base does not exist
- **THEN** system prints "Knowledge base 'unknown-kb' not found"

#### Scenario: Upload file that doesn't exist locally
- **WHEN** user runs `kb upload my-docs /path/to/nonexistent.pdf`
- **THEN** system prints "File not found: /path/to/nonexistent.pdf"

#### Scenario: Overwrite existing file
- **WHEN** user runs `kb upload my-docs report.pdf` and `report.pdf` already exists in the knowledge base
- **THEN** the old file copy is overwritten
- **THEN** old vectors are deleted from ChromaDB
- **THEN** the file is re-parsed, re-chunked, and re-indexed
- **THEN** system prints "Re-indexed report.pdf (X chunks)"

### Requirement: User SHALL delete a file from a knowledge base

The system SHALL remove the file copy and its corresponding vectors from the knowledge base.

#### Scenario: Delete an existing file
- **WHEN** user runs `python -m app.kb_manager.cli kb delete my-docs report.pdf`
- **THEN** `kb/my-docs/files/report.pdf` is deleted
- **THEN** all vectors with metadata `file_name=report.pdf` are deleted from ChromaDB
- **THEN** system prints "Deleted report.pdf (X vectors removed)"

#### Scenario: Delete non-existent file
- **WHEN** user runs `kb delete my-docs missing.pdf` and the file is not in the knowledge base
- **THEN** system prints "File 'missing.pdf' not found in knowledge base 'my-docs'"

### Requirement: User SHALL reindex a file in a knowledge base

The system SHALL delete existing vectors for a file and re-index it from the stored copy.

#### Scenario: Reindex an existing file
- **WHEN** user runs `python -m app.kb_manager.cli kb reindex my-docs report.pdf`
- **THEN** old vectors with metadata `file_name=report.pdf` are deleted
- **THEN** `kb/my-docs/files/report.pdf` is re-parsed and re-indexed
- **THEN** system prints "Reindexed report.pdf (X chunks)"

### Requirement: User SHALL list files in a knowledge base

The system SHALL display all files stored in a knowledge base.

#### Scenario: List files in existing knowledge base
- **WHEN** user runs `python -m app.kb_manager.cli kb list my-docs`
- **THEN** system lists all filenames in `kb/my-docs/files/` with their sizes

#### Scenario: List all knowledge bases
- **WHEN** user runs `python -m app.kb_manager.cli kb list`
- **THEN** system lists all knowledge base directories under `kb/`

## ADDED Requirements

### Requirement: User SHALL index a file by name

The system SHALL parse, chunk, embed, and store vectors for a previously uploaded file.

#### Scenario: Index a single file
- **WHEN** user runs `python -m app.modules.kb_manager.cli kb index my-docs report.pdf`
- **THEN** the file `kb/my-docs/files/report.pdf` is parsed and indexed
- **THEN** vectors are stored in `kb/my-docs/vector_db/`
- **THEN** system prints "Indexed report.pdf (X chunks)"

#### Scenario: Index non-existent file
- **WHEN** user runs `kb index my-docs missing.pdf` and the file was not uploaded
- **THEN** system prints "File 'missing.pdf' not found in knowledge base 'my-docs'"

### Requirement: User SHALL index a folder by name

The system SHALL batch-index all files recorded in the folder map.

#### Scenario: Index a folder
- **WHEN** user runs `python -m app.modules.kb_manager.cli kb index my-docs my-folder`
- **THEN** the folder map `_folder_map.json` is read
- **THEN** each file in the folder is indexed sequentially
- **THEN** system prints progress for each file

### Requirement: User SHALL index all unindexed files

The system SHALL support indexing all files in the knowledge base that have not been indexed yet.

#### Scenario: Index all
- **WHEN** user runs `python -m app.modules.kb_manager.cli kb index my-docs --all`
- **THEN** all files in `kb/my-docs/files/` (excluding `_folder_map.json`) are indexed

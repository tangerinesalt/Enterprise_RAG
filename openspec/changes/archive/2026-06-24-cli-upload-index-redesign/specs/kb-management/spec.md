## MODIFIED Requirements

### Requirement: User SHALL upload a file to a knowledge base

**Previous behavior**: Upload copies the file AND indexes it in one step.
**New behavior**: Upload ONLY copies the file. Indexing is a separate step via `kb index`.

The system SHALL copy a file into the knowledge base's file storage without automatic indexing.

#### Scenario: Upload a new file
- **WHEN** user runs `python -m app.modules.kb_manager.cli kb upload my-docs /path/to/report.pdf`
- **THEN** the file is copied to `kb/my-docs/files/report.pdf`
- **THEN** no indexing is performed
- **THEN** system prints "Copied: report.pdf"

#### Scenario: Upload file to non-existent knowledge base
- **WHEN** user runs `kb upload unknown-kb file.pdf` and the knowledge base does not exist
- **THEN** system prints "Knowledge base 'unknown-kb' not found"

#### Scenario: Overwrite existing file
- **WHEN** user runs `kb upload my-docs report.pdf` and `report.pdf` already exists
- **THEN** the old file copy is silently overwritten
- **THEN** old vectors are NOT deleted (user must run `kb reindex` or `kb index` to update)

### Requirement: User SHALL delete a file or folder from a knowledge base

The system SHALL remove the file copy (or folder recursively) and all corresponding vectors.

#### Scenario: Delete an existing file
- **WHEN** user runs `python -m app.modules.kb_manager.cli kb delete my-docs report.pdf`
- **THEN** `kb/my-docs/files/report.pdf` is deleted
- **THEN** all vectors for `report.pdf` are deleted from ChromaDB
- **THEN** system prints "Deleted report.pdf (X vectors removed)"

#### Scenario: Delete an existing folder
- **WHEN** user runs `python -m app.modules.kb_manager.cli kb delete my-docs my-folder`
- **THEN** `kb/my-docs/files/my-folder/` directory is recursively scanned for all files
- **THEN** each file's vectors are deleted from ChromaDB
- **THEN** each file is removed from disk
- **THEN** the `my-folder/` directory itself is deleted
- **THEN** system prints "Deleted folder 'my-folder' (X files, Y vectors removed)"

## ADDED Requirements

### Requirement: User SHALL upload a folder to a knowledge base

The system SHALL recursively copy a folder's contents into the knowledge base's file storage, preserving directory structure.

#### Scenario: Upload a folder
- **WHEN** user runs `python -m app.modules.kb_manager.cli kb upload my-docs /path/to/my-folder`
- **THEN** the folder `my-folder/` is created under `kb/my-docs/files/my-folder/`
- **THEN** all files are copied preserving subdirectory structure
- **THEN** no indexing is performed
- **THEN** system prints count of files copied

## ADDED Requirements

### Requirement: User SHALL upload and index in one step

The system SHALL provide a convenience command that copies a file and immediately indexes it.

#### Scenario: Upload-and-index a file
- **WHEN** user runs `python -m app.modules.kb_manager.cli kb upload-and-index my-docs /path/to/report.pdf`
- **THEN** the file is copied to `kb/my-docs/files/report.pdf`
- **THEN** the file is immediately parsed, chunked, embedded, and stored
- **THEN** system prints "Uploaded and indexed report.pdf (X chunks)"

#### Scenario: Upload-and-index a folder
- **WHEN** user runs `python -m app.modules.kb_manager.cli kb upload-and-index my-docs /path/to/my-folder`
- **THEN** the folder is uploaded (flattened with prefix)
- **THEN** all files are indexed
- **THEN** system prints summary

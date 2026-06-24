## ADDED Requirements

### Requirement: Folder upload SHALL preserve directory structure

When uploading a folder, the system SHALL preserve the original directory structure inside `kb/<name>/files/`.

#### Scenario: Upload folder with subdirectories
- **WHEN** user uploads folder `my-folder/` containing `doc1.txt` and `sub/doc2.txt`
- **THEN** `kb/<name>/files/my-folder/doc1.txt` is created
- **THEN** `kb/<name>/files/my-folder/sub/doc2.txt` is created

#### Scenario: Upload single file mixed with folder
- **WHEN** user uploads `report.pdf` to the same knowledge base
- **THEN** `kb/<name>/files/report.pdf` is created as a flat file
- **THEN** the existing `my-folder/` directory is untouched

### Requirement: Folder operations SHALL be recursive

Both index and delete operations on a folder SHALL recursively process all files within it.

#### Scenario: Index folder recursively
- **WHEN** user runs `kb index my-docs my-folder`
- **THEN** all files under `kb/<name>/files/my-folder/` are indexed, including subdirectories

#### Scenario: Delete folder recursively
- **WHEN** user runs `kb delete my-docs my-folder`
- **THEN** all files under `kb/<name>/files/my-folder/` have their vectors deleted
- **THEN** all files are removed from disk
- **THEN** `kb/<name>/files/my-folder/` directory itself is removed

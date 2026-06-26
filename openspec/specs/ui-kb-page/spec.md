## Purpose

Define the React knowledge base pages for listing, creating, uploading, indexing, and deleting KB content.

## Requirements

### Requirement: KB list page SHALL show all knowledge bases

The page SHALL display all KBs with file/folder counts and create/delete operations.

#### Scenario: List all KBs
- **WHEN** user visits `/kb`
- **THEN** all knowledge bases are displayed with name and file/folder counts
- **THEN** a "+" button is visible for creating new KBs

#### Scenario: Delete a KB
- **WHEN** user clicks the delete button on a KB row
- **THEN** the KB is deleted after confirmation

### Requirement: KB detail page SHALL show files and folders

The page SHALL display all files/folders in a KB and support upload, delete, index.

#### Scenario: View KB details
- **WHEN** user clicks a KB row
- **THEN** the page shows all files and folders in that KB

#### Scenario: Upload files
- **WHEN** user clicks upload button and selects files
- **THEN** files are uploaded via `POST /api/kb/upload`

#### Scenario: Index a file
- **WHEN** user clicks index button on a file row
- **THEN** the file is indexed via `POST /api/kb/index`

#### Scenario: Delete a file
- **WHEN** user clicks delete on a file/folder row
- **THEN** the file/folder is deleted

#### Scenario: Upload folder
- **WHEN** user clicks upload folder button
- **THEN** the folder is uploaded with directory structure preserved

## MODIFIED Requirements

### Requirement: API SHALL create a knowledge base

The system SHALL create a new knowledge base via REST API, and the provided knowledge base name SHALL satisfy the system's path-safe identifier rules.

#### Scenario: POST /api/kb
- **WHEN** client sends `POST /api/kb` with body `{"name": "my-docs"}`
- **THEN** a new KB is created
- **THEN** response returns `{"ok": true, "data": {"name": "my-docs"}}`

#### Scenario: POST /api/kb rejects unsafe name
- **WHEN** client sends `POST /api/kb` with a knowledge base name containing path separators, `..`, or absolute-path semantics
- **THEN** the API rejects the request
- **THEN** no directory is created outside or inside the KB root for that invalid name

### Requirement: API SHALL delete a knowledge base

The system SHALL delete a knowledge base, and the requested knowledge base name SHALL resolve only within the configured KB root.

#### Scenario: DELETE /api/kb/{name}
- **WHEN** client sends `DELETE /api/kb/my-docs`
- **THEN** the KB directory is removed
- **THEN** response returns `{"ok": true}`

#### Scenario: DELETE /api/kb/{name} rejects unsafe name
- **WHEN** client sends `DELETE /api/kb/{name}` using a knowledge base name with path traversal or absolute-path semantics
- **THEN** the API rejects the request
- **THEN** no directory outside the KB root is removed

## ADDED Requirements

### Requirement: API SHALL upload files only within the target knowledge base root

The system SHALL store uploaded files only under the target knowledge base's file root. For Web uploads, the API SHALL first reduce the client-provided filename to a leaf filename, then validate that leaf filename, and SHALL reject the file if the resulting leaf filename is invalid.

#### Scenario: POST /api/kb/upload stores file in KB root
- **WHEN** client sends `POST /api/kb/upload` with a valid knowledge base name and file payload
- **THEN** the API stores the file under `kb/<name>/files/`
- **THEN** the file status is marked pending

#### Scenario: POST /api/kb/upload rejects unsafe filename
- **WHEN** client uploads a file whose client-provided filename contains traversal or absolute-path semantics
- **THEN** the API strips path components and evaluates only the resulting leaf filename
- **THEN** if that leaf filename is valid, the file is stored under `kb/<name>/files/`
- **THEN** if that leaf filename is invalid, the API rejects the file
- **THEN** no file is written outside `kb/<name>/files/`

### Requirement: API SHALL upload-and-index files only within the target knowledge base root

The system SHALL ensure the upload-and-index endpoint never creates directories or files outside the target knowledge base root. For Web uploads, the endpoint SHALL apply the same leaf-filename reduction and leaf-name validation rules as the plain upload endpoint.

#### Scenario: POST /api/kb/upload-and-index writes only inside KB root
- **WHEN** client sends `POST /api/kb/upload-and-index` with valid files for an existing knowledge base
- **THEN** each accepted file is written only under that knowledge base's file root
- **THEN** indexing runs only against those accepted in-root files

#### Scenario: POST /api/kb/upload-and-index rejects out-of-root target
- **WHEN** client-provided filename intent would normalize outside the knowledge base file root
- **THEN** the API strips path components and evaluates only the resulting leaf filename
- **THEN** if the resulting leaf filename is invalid, the API rejects the file
- **THEN** no out-of-root directory or file is created

### Requirement: API SHALL delete files only within the target knowledge base root

The system SHALL delete files from a knowledge base only when the requested filename resolves within that knowledge base's file root.

#### Scenario: DELETE /api/kb/{name}/files deletes in-root file
- **WHEN** client sends `DELETE /api/kb/{name}/files?filename=report.pdf`
- **THEN** the API deletes `report.pdf` from the target knowledge base
- **THEN** related vectors and file status are removed

#### Scenario: DELETE /api/kb/{name}/files rejects unsafe filename
- **WHEN** client sends a filename that would resolve outside the target knowledge base root
- **THEN** the API rejects the request
- **THEN** no file outside that root is deleted

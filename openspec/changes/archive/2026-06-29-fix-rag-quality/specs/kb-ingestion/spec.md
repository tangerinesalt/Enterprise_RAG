## MODIFIED Requirements

### Requirement: Document parsing SHALL strip BOM

The document parser SHALL remove UTF-8 BOM (`﻿`) from document text before chunking and embedding.

#### Scenario: TXT file with BOM header
- **WHEN** a .txt source file contains `﻿` (UTF-8 BOM) at position 0
- **THEN** the resulting chunk text does NOT contain `﻿`
- **THEN** the vector stored in ChromaDB does NOT contain `﻿`
- **THEN** the source text displayed in chat does NOT contain `﻿`

#### Scenario: PDF text extraction with BOM
- **WHEN** a PDF page extracts text that contains BOM
- **THEN** the BOM is stripped during chunking
- **THEN** no downstream data contains BOM

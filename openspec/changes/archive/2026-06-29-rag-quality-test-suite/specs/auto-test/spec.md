## MODIFIED Requirements

### Requirement: Test script SHALL validate end-to-end CLI workflow

The system SHALL provide `test/test_auto.py` that creates test data and verifies upload → index → query → delete, including embedding quality checks.

#### Scenario: Full workflow test with embedding quality check
- **WHEN** `python test/test_auto.py` is run
- **THEN** a test knowledge base is created and populated with test files
- **THEN** each topic (A1-A4) is queried and responses verified (unchanged)
- **THEN** a retrieval diagnostic is run via `test_retrieval_diagnostic.py` subprocess call
- **THEN** the diagnostic output is checked for anomalies E01 and E03
- **THEN** if either anomaly is detected, the test prints a WARNING but does not fail
- **THEN** the knowledge base is cleaned up

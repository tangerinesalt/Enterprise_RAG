## ADDED Requirements

### Requirement: Test script SHALL validate end-to-end CLI workflow

The system SHALL provide `test/test_auto.py` that creates test data and verifies upload → index → query → delete.

#### Scenario: Full workflow test
- **WHEN** `python test/test_auto.py` is run
- **THEN** a test directory is created on the desktop at `rag-test/`
- **THEN** test files are created covering A1, A2, A3, A4 topics
- **THEN** a knowledge base is created and the folder is uploaded
- **THEN** the folder is indexed
- **THEN** each topic (A1-A4) is queried
- **THEN** each response is verified to contain expected keywords
- **THEN** the knowledge base is cleaned up (files + vectors deleted)
- **THEN** the desktop test directory is deleted
- **THEN** a pass/fail report is printed

#### Scenario: Test data layout
- **WHEN** the test runs
- **THEN** `%USERPROFILE%/Desktop/rag-test/` contains:
  - `A1-概述.txt` with content answering "什么是A1？"
  - `A2-原理.txt` with content answering "什么是A2？"
  - `sub/A3-应用.txt` with content answering "什么是A3？"
  - `sub/A4-实践.txt` with content answering "什么是A4？"

#### Scenario: Retrieval diagnostic runs after indexing
- **WHEN** indexing completes
- **THEN** `test_retrieval_diagnostic.py` is called as a subprocess with the test KB and query
- **THEN** diagnostic output is checked for anomalies E01 and E03
- **THEN** if either anomaly is detected, a WARNING is printed (test does not fail)

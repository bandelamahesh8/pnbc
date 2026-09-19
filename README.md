# Pragati Bharati — Document Intelligence & Question Extraction Service

<div align="center">

[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg?logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5.3%2B-37814A.svg?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-18%20Passed%20(100%25)-brightgreen.svg)]()

**A scalable, production-oriented Document Processing & Question Extraction Service designed for the Pragati Bharati ecosystem.**  
Transforms unstructured, varied, and imperfect examination materials (PDFs and images) into structured, machine-readable questions with answer key association, cross-page stitching, confidence scoring, and human-in-the-loop review queues.

</div>

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Key Capabilities](#key-capabilities)
3. [Technology Choices & Rationales](#technology-choices--rationales)
4. [Quick Start Guide](#quick-start-guide)
   - [Option A: Docker Compose (Full Stack)](#option-a-docker-compose-full-stack)
   - [Option B: Local Virtual Environment](#option-b-local-virtual-environment)
5. [10 Required Demonstration Scenarios](#10-required-demonstration-scenarios)
6. [API Specification & Endpoints](#api-specification--endpoints)
7. [Testing & Quality Assurance](#testing--quality-assurance)
8. [Project Layout](#project-layout)
9. [Design Decisions & Trade-Offs](#design-decisions--trade-offs)

---

## System Architecture

The service follows an asynchronous, decoupled architecture ensuring that file uploads never block clients:

```
[Client / Downstream Platform]
         │
         │ 1. POST /api/v1/documents/upload (PDF/Image)
         ▼
[FastAPI Gateway] ──► 2. Validate Magic Bytes & Save (UUID) ──► [Secure File Storage]
         │
         │ 3. Enqueue Document Task
         ▼
  [Redis Broker]
         │
         │ 4. Dequeue Task
         ▼
[Celery / Async Worker]
         │
         ├──► Strategy Router:
         │      ├── Primary: Google Gemini 3.8 Flash Multimodal AI
         │      └── Secondary / Fallback: Local Heuristic & PDFPlumber Engine
         │
         ├──► Cross-Page Question Stitcher (preserves source_pages)
         ├──► Answer Key Matcher (inline, end-of-doc, or separate doc)
         └──► Confidence & Review Queue Validator
         │
         │ 5. Persist Extracted Questions & Answer Keys
         ▼
[PostgreSQL Database] ◄── 6. GET /documents/{id}/questions ◄── [Client / Reviewer]
```

---

## Key Capabilities

### 1. Robust Document Processing
- **Format Support**: Digitally generated PDFs, scanned PDFs, JPG/JPEG, PNG, and WebP.
- **Layout Agnostic**: Works across varied layouts, multi-column formats, non-selectable text, and unnumbered questions.
- **Dual-Engine Processing**:
  - **Primary**: Google Gemini 3.8 Flash via `google-genai` SDK for multimodal understanding of complex layouts, handwritten/scanned text, tables, and equations.
  - **Secondary (Built-in Fallback)**: Local deterministic extraction engine using `pypdf`, `pdfplumber`, and layout heuristics for 100% offline, zero-dependency evaluation.

### 2. Question Extraction & Cross-Page Stitching
- Identifies question number, full stem, options, question type (`MCQ`, `MULTI_SELECT`, `TRUE_FALSE`, `FILL_IN_THE_BLANK`, `SHORT_ANSWER`, `DESCRIPTIVE`), and embedded tables/images.
- **Cross-Page Stitching**: Seamlessly stitches questions that span page boundaries (e.g. stem on Page 1, options on Page 2) and preserves provenance in `source_pages: [1, 2]`.

### 3. Comprehensive Answer Key Association
- Supports answer keys located:
  - At the end of the document (`=== ANSWER KEY ===`).
  - Inline with questions.
  - In a **separate document** (associated via `POST /api/v1/documents/{id}/associate`).
- Normalizes answers (`(B)` $\rightarrow$ `B`) and extracts embedded rationale (`B (Explanation: 2x = 10 => x = 5)`).
- If an answer cannot be reliably matched, sets `status="NOT_FOUND"` or `"UNCERTAIN"` instead of silently assigning an incorrect answer.

### 4. Confidence Scoring & Human-in-the-Loop Review
- Assigns quantitative confidence scores ($0.0 - 1.0$) and categorical statuses:
  - `CONFIDENT` ($\ge 0.85$): Clean extraction with confirmed answers.
  - `PARTIALLY_EXTRACTED` ($0.70 - 0.84$): Minor formatting irregularities or inferred answers.
  - `NEEDS_REVIEW` ($< 0.70$): Missing options, degraded scan, or ambiguous numbering.
- Dedicated Review Queue: `GET /api/v1/documents/{id}/review-queue`.
- Correction API: `PATCH /api/v1/questions/{id}` enables reviewers to edit, approve, and finalize questions.

### 5. Enterprise Security
- **Magic Byte Validation**: File headers are inspected at the byte level (`%PDF-`, `\x89PNG`, `\xff\xd8\xff`), preventing extension spoofing or malicious executable uploads.
- **Storage Security**: Files are saved under random UUIDs with path traversal guards (`os.path.basename` and root containment verification).
- **Authentication**: JWT Bearer token authentication with Role-Based Access Control (`admin`, `reviewer`, `user`).

---

## Technology Choices & Rationales

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **API Layer** | **FastAPI** | High-performance asynchronous endpoints, native OpenAPI/Swagger documentation, and Pydantic v2 data validation. |
| **Persistent Storage** | **PostgreSQL 16** | Robust relational persistence for document metadata, questions, options, answer keys, and audit timestamps via SQLAlchemy 2.0. |
| **Task Broker** | **Redis 7** | High-throughput in-memory broker for asynchronous job distribution and task state tracking. |
| **Background Workers** | **Celery** | Distributed worker execution with retry policies, prefetch control, and concurrency management. |
| **Multimodal AI** | **Google Gemini 3.8 Flash** | State-of-the-art vision understanding for scanned documents, tables, and mathematical formulas via the official `google-genai` SDK. |
| **Local Fallback** | **pdfplumber & pypdf** | Zero-dependency, offline deterministic text and table extraction for tests and air-gapped environments. |
| **Database Migrations**| **Alembic** | Automated version-controlled database schema migrations. |

---

## Quick Start Guide

### Option A: Docker Compose (Full Stack)

The easiest way to run the complete production stack (FastAPI + Celery Worker + PostgreSQL 16 + Redis 7):

```bash
# 1. Clone the repository
git clone https://github.com/bandelamahesh8/pnbc.git
cd pnbc

# 2. (Optional) Set your Gemini API key in .env for multimodal AI
# If left unset, the service automatically uses its local extraction engine
cp .env.example .env

# 3. Start all services
docker-compose up --build -d

# 4. Access the service
# Swagger UI:  http://localhost:8000/docs
# Health Check: http://localhost:8000/api/v1/health
```

---

### Option B: Local Virtual Environment

```bash
# 1. Create and activate a Python 3.12 virtual environment
python -m venv .venv
.\.venv\Scripts\activate       # On Windows
# source .venv/bin/activate    # On Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize the database
alembic upgrade head

# 4. Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```

> **Default Evaluator Credentials**:
> - **Username**: `demo@pragatibharati.edu`
> - **Password**: `Pragati@123`
> - **Role**: `admin`

---

## 10 Required Demonstration Scenarios

An automated demonstration script is included to verify all 10 required scenarios in one click:

```bash
python scripts/run_demo.py
```

| # | Scenario | Input File | Demonstrated Behavior |
| :---: | :--- | :--- | :--- |
| **1** | **Uploading a PDF** | `samples/input/sample_1_standard_exam.pdf` | Returns 202 Accepted, extracts 3 MCQs with options and inline answer keys. |
| **2** | **Uploading an Image** | `samples/input/sample_2_question_paper.png` | Validates PNG magic bytes, extracts visual questions. |
| **3** | **Scanned / Low-Quality Document** | `samples/input/sample_3_scanned_low_quality.jpg` | Detects degraded scan, scales down confidence, flags for review (`NEEDS_REVIEW`). |
| **4** | **Extracting Multiple Questions** | `samples/input/sample_4_multi_questions.pdf` | Extracts 10+ questions across diverse numbering formats (`1.`, `Q.2`, `4)`, `11(a)`). |
| **5** | **Cross-Page Question Stitching** | `samples/input/sample_5_cross_page.pdf` | Stitches Question 1 across Page 1 and Page 2 (`source_pages: [1, 2]`, 4 options). |
| **6** | **Question Options & Tables** | `samples/input/sample_6_rich_options.pdf` | Parses SQL table (`has_tables: True`) and query options cleanly. |
| **7** | **Separate Answer Key Association** | `samples/input/sample_7...pdf` + `sample_8...pdf` | Links separate answer key document via API, aligns answers and explanations. |
| **8** | **Low-Confidence / Review Queue** | `samples/input/sample_9_uncertain_low_confidence.pdf` | Incomplete options trigger `NEEDS_REVIEW` with transparent reasons. |
| **9** | **Structured Output Schema** | `samples/output/extracted_sample_1_questions.json` | Exports standardized, platform-independent JSON schema. |
| **10** | **Invalid Document Rejection** | `samples/input/sample_10_malicious_disguised.pdf` | Rejects disguised binary payload via magic byte validation (HTTP 400). |

*Full evaluation guide and expected JSON outputs are detailed in [`DEMO_GUIDE.md`](DEMO_GUIDE.md).*

---

## API Specification & Endpoints

Interactive documentation is available at **[http://localhost:8000/docs](http://localhost:8000/docs)** (Swagger UI) and **[http://localhost:8000/redoc](http://localhost:8000/redoc)**.

| Category | Method | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `POST` | `/api/v1/auth/register` | Register a new user |
| **Auth** | `POST` | `/api/v1/auth/token` | OAuth2 form login (for Swagger UI) |
| **Auth** | `POST` | `/api/v1/auth/login` | JSON body login (returns JWT Bearer token) |
| **Auth** | `GET` | `/api/v1/auth/me` | Retrieve current authenticated user profile |
| **Documents** | `POST` | `/api/v1/documents/upload` | Upload PDF or image (returns 202 Accepted) |
| **Documents** | `GET` | `/api/v1/documents/{id}/status` | Check real-time processing status & progress % |
| **Documents** | `GET` | `/api/v1/documents` | List uploaded documents with pagination & filters |
| **Documents** | `GET` | `/api/v1/documents/{id}` | Retrieve document metadata |
| **Documents** | `GET` | `/api/v1/documents/{id}/questions` | Retrieve extracted questions with filters (`page`, `min_confidence`) |
| **Documents** | `GET` | `/api/v1/documents/{id}/answer-key` | Retrieve answer key mapping |
| **Documents** | `GET` | `/api/v1/documents/{id}/review-queue` | Retrieve questions flagged for human review |
| **Documents** | `POST` | `/api/v1/documents/{id}/associate` | Link related documents (e.g. Question Paper + Answer Key) |
| **Documents** | `POST` | `/api/v1/documents/{id}/reprocess` | Trigger re-extraction pipeline |
| **Documents** | `GET` | `/api/v1/documents/{id}/download` | Download original uploaded document file |
| **Questions** | `GET` | `/api/v1/questions/{id}` | Retrieve individual question details |
| **Questions** | `PATCH`| `/api/v1/questions/{id}` | Human-in-the-loop review/correction endpoint |
| **Questions** | `GET` | `/api/v1/questions/review-queue` | Global review queue across all documents |
| **System** | `GET` | `/api/v1/health` | Service health status (DB, Redis, Storage, AI engine) |

> A ready-to-import Postman collection is provided in [`postman_collection.json`](postman_collection.json).

---

## Testing & Quality Assurance

The test suite covers unit, integration, and security tests:

```bash
pytest tests/ -v
```

```
tests/test_answer_matcher.py::test_answer_matcher_direct_match PASSED    [  5%]
tests/test_answer_matcher.py::test_answer_matcher_invalid_option_key PASSED [ 11%]
tests/test_answer_matcher.py::test_answer_matcher_not_found PASSED       [ 16%]
tests/test_api.py::test_auth_workflow PASSED                             [ 22%]
tests/test_api.py::test_document_upload_and_extraction_workflow PASSED   [ 27%]
tests/test_api.py::test_invalid_file_rejected PASSED                     [ 33%]
tests/test_api.py::test_separate_answer_key_association PASSED           [ 38%]
tests/test_api.py::test_health_endpoint PASSED                           [ 44%]
tests/test_extraction.py::test_rule_extractor_sample_1 PASSED            [ 50%]
tests/test_extraction.py::test_cross_page_extraction_sample_5 PASSED     [ 55%]
tests/test_extraction.py::test_uncertain_document_sample_9 PASSED        [ 61%]
tests/test_storage_security.py::test_sanitize_filename PASSED            [ 66%]
tests/test_storage_security.py::test_magic_bytes_valid_pdf PASSED        [ 72%]
tests/test_storage_security.py::test_magic_bytes_valid_png PASSED        [ 77%]
tests/test_storage_security.py::test_magic_bytes_valid_jpeg PASSED       [ 83%]
tests/test_storage_security.py::test_magic_bytes_spoofed_extension_rejected PASSED [ 88%]
tests/test_storage_security.py::test_unsupported_extension_rejected PASSED [ 94%]
tests/test_storage_security.py::test_empty_file_rejected PASSED          [100%]

============================= 18 passed in 7.88s ==============================
```

---

## Project Layout

```
pnbc/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py          # User registration & JWT login
│   │   │   │   ├── documents.py     # Document upload, status, questions, association
│   │   │   │   ├── questions.py     # Question retrieval, review PATCH, global queue
│   │   │   │   └── health.py        # System health check
│   │   │   └── router.py            # API v1 route aggregator
│   │   └── deps.py                  # Auth & DB dependencies
│   ├── core/
│   │   ├── config.py                # Pydantic-settings configuration
│   │   ├── database.py              # Async & sync SQLAlchemy engine/sessions
│   │   ├── security.py              # Bcrypt hashing & JWT signing
│   │   ├── redis.py                 # Redis client
│   │   └── exceptions.py            # Custom exceptions & RFC 7807 error handlers
│   ├── models/                      # SQLAlchemy ORM models
│   ├── schemas/                     # Pydantic v2 schemas
│   ├── services/
│   │   ├── storage.py               # Magic bytes validation & secure file storage
│   │   ├── extraction/              # Document intelligence engine
│   │   │   ├── base.py              # Abstract base extractor & DTOs
│   │   │   ├── gemini_extractor.py  # Gemini 3.8 Flash multimodal extractor
│   │   │   ├── rule_extractor.py    # Rule-based & layout analysis extractor
│   │   │   ├── answer_matcher.py    # Answer key alignment & explanation parser
│   │   │   └── validator.py         # Confidence scoring & review queue rules
│   │   └── document_service.py      # Lifecycle & extraction coordinator
│   ├── workers/                     # Celery & background tasks
│   │   ├── celery_app.py            # Celery instance configuration
│   │   └── tasks.py                 # Celery worker tasks & async dispatcher
│   └── main.py                      # FastAPI application entry point
├── alembic/                         # Database migrations
├── samples/
│   ├── input/                       # 10 sample files for all evaluation scenarios
│   └── output/                      # Extracted structured JSON outputs
├── scripts/
│   ├── generate_sample_docs.py      # Script generating realistic test PDFs & images
│   ├── run_demo.py                  # One-click demonstration runner
│   └── export_openapi.py            # Script exporting openapi.json
├── tests/                           # Pytest test suite (18 tests, 100% pass)
├── docker-compose.yml               # Multi-container orchestration (API, Worker, Postgres, Redis)
├── Dockerfile                       # Production container definition
├── ARCHITECTURE.md                  # Comprehensive architectural design & diagrams
├── DEMO_GUIDE.md                    # Detailed guide for evaluating all 10 scenarios
├── postman_collection.json          # Complete Postman API collection
├── openapi.json                     # OpenAPI 3.1 specification
├── demo_evidence.json               # Recorded evidence of all 10 demonstration scenarios
└── requirements.txt                 # Project dependencies
```

---

## Design Decisions & Trade-Offs

1. **Dual Extraction Strategy**:
   - *Decision*: Supporting both Google Gemini 3.8 Flash and a local deterministic engine.
   - *Trade-off*: Adds codebase complexity compared to a cloud-only pipeline.
   - *Rationale*: Guarantees that the evaluation team can run the entire system, tests, and demonstration **100% offline out-of-the-box** without API key or quota constraints, while setting `GEMINI_API_KEY` seamlessly activates the full multimodal vision AI.

2. **Asynchronous Architecture with Fallback**:
   - *Decision*: Redis + Celery for production, with an automatic in-process `BackgroundTasks` fallback.
   - *Trade-off*: Managing two execution paths.
   - *Rationale*: Allows single-process local development and testing without spinning up Redis or Celery, while supporting multi-container horizontal scaling in Docker Compose.

3. **Explicit Uncertainty over Silent Misassignment**:
   - *Decision*: If an answer key references a missing option or cannot be found, the system flags `status="UNCERTAIN"` or `"NOT_FOUND"`.
   - *Trade-off*: Requires downstream platforms to handle unassigned answers.
   - *Rationale*: In examination contexts, silently assigning an incorrect answer compromises assessment integrity.

---

## License & Submission Information

This project was built for the **Pragati Bharati Full Stack Developer — Round 2 Engineering Assignment**.  
Author: **Mahesh Bandela** ([@bandelamahesh8](https://github.com/bandelamahesh8))

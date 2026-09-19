# Pragati Bharati — Document Intelligence & Question Extraction Service

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5.3+-37814A.svg)](https://docs.celeryq.dev/)
[![Tests](https://img.shields.io/badge/tests-18%20passed-brightgreen.svg)]()

Production-grade, scalable **Document Processing & Question Extraction Service** built for **Pragati Bharati**. Accepts PDF documents and images containing examination material and converts them into structured, machine-readable questions with answer key association, cross-page stitching, confidence scoring, and human-in-the-loop review queues.

---

## Key Features

- **Asynchronous Document Processing**: Uploads return `202 Accepted` immediately with status tracking URLs.
- **Dual-Engine Extraction**:
  - **Primary**: Google Gemini 3.8 Flash Multimodal AI (`google-genai` SDK) for deep layout, equation, table, and degraded scan understanding.
  - **Secondary**: Local deterministic rule-based extractor (`pypdf`, `pdfplumber`, `pillow`) for 100% offline, zero-dependency execution and testing.
- **Cross-Page Question Stitching**: Seamlessly stitches question stems and options that span page boundaries.
- **Answer Key Association**: Correlates inline answer keys, solutions at the end of documents, or separate answer key documents (`POST /documents/{id}/associate`).
- **Confidence Scoring & Review Queue**: Quantitative confidence ratings ($0.0 - 1.0$) and automated flagging for human review (`NEEDS_REVIEW`) with transparent reasons.
- **Human-in-the-Loop Review API**: Endpoints to edit, approve, or update extracted questions (`PATCH /questions/{id}`).
- **Enterprise Security**:
  - OAuth2 Password Bearer flow with JWT authentication and role-based access control.
  - Magic byte (file signature) validation preventing disguised or malicious uploads.
  - UUID-based file storage and strict path traversal protection.

---

## Project Structure

```
PNBC/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── auth.py          # User registration & JWT login
│   │   │   │   ├── documents.py     # Document upload, status, questions, association
│   │   │   │   ├── questions.py     # Question retrieval, PATCH review, global queue
│   │   │   │   └── health.py        # Health check endpoint
│   │   │   └── router.py            # API v1 router
│   │   └── deps.py                  # Auth & DB dependencies
│   ├── core/
│   │   ├── config.py                # Pydantic-settings configuration
│   │   ├── database.py              # Async & sync SQLAlchemy sessions
│   │   ├── security.py              # Password hashing & JWT tokens
│   │   ├── redis.py                 # Redis client connection
│   │   └── exceptions.py            # Custom exceptions & RFC 7807 handlers
│   ├── models/                      # SQLAlchemy ORM models
│   ├── schemas/                     # Pydantic v2 schemas
│   ├── services/
│   │   ├── storage.py               # Magic bytes validation & secure storage
│   │   ├── extraction/              # Document intelligence engine
│   │   │   ├── base.py              # Abstract base extractor & DTOs
│   │   │   ├── gemini_extractor.py  # Gemini 3.8 Flash multimodal extractor
│   │   │   ├── rule_extractor.py    # Rule-based & layout analysis extractor
│   │   │   ├── answer_matcher.py    # Answer key alignment & normalizer
│   │   │   └── validator.py         # Confidence scoring & review queue rules
│   │   └── document_service.py      # Lifecycle & extraction coordinator
│   ├── workers/                     # Celery & background tasks
│   │   ├── celery_app.py            # Celery instance configuration
│   │   └── tasks.py                 # Worker tasks & async dispatcher
│   └── main.py                      # FastAPI app entry point
├── alembic/                         # Database migrations
├── samples/
│   ├── input/                       # Sample PDFs and images for all 10 scenarios
│   └── output/                      # Extracted structured JSON outputs
├── scripts/
│   ├── generate_sample_docs.py      # Generates realistic test PDFs & images
│   ├── run_demo.py                  # One-click demo runner for all 10 scenarios
│   └── export_openapi.py            # Exports openapi.json
├── tests/                           # Pytest test suite (18 tests, 100% pass)
├── docker-compose.yml               # Multi-container orchestration (API, Worker, Postgres, Redis)
├── Dockerfile                       # Production container definition
├── ARCHITECTURE.md                  # Comprehensive architectural design & diagrams
├── DEMO_GUIDE.md                    # Detailed guide for evaluating all 10 scenarios
├── postman_collection.json          # Complete Postman API collection
├── openapi.json                     # OpenAPI 3.1 specification
└── requirements.txt                 # Project dependencies
```

---

## Quickstart Guide

### Option A: Local Setup (Fastest for Evaluation)

1. **Clone or Navigate to the Workspace**:
   ```bash
   cd PNBC
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate   # On Windows
   # source .venv/bin/activate # On Linux/macOS
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**:
   ```bash
   alembic upgrade head
   ```

5. **Run the API Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
   - Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### Option B: Docker Compose (Full Stack with PostgreSQL & Redis)

To run the complete production stack (FastAPI + Celery Worker + PostgreSQL 16 + Redis 7):

```bash
docker-compose up --build -d
```

Check service logs:
```bash
docker-compose logs -f api worker
```

---

## Running the Automated Demonstration

To execute all 10 demonstration scenarios end-to-end with verified evidence:

```bash
.\.venv\Scripts\python scripts/run_demo.py
```

This generates `demo_evidence.json` and extracts sample questions into `samples/output/extracted_sample_1_questions.json`.

---

## Running Automated Tests

```bash
.\.venv\Scripts\pytest -v
```

All 18 tests pass with 100% success rate.

---

## Default Evaluator Credentials

On initial startup, the service automatically seeds a default demo user:
- **Email**: `demo@pragatibharati.edu`
- **Password**: `Pragati@123`
- **Role**: `admin`

---

## Core API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/token` | OAuth2 login / obtain Bearer token |
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/documents/upload` | Upload PDF or image (returns 202 Accepted) |
| `GET` | `/api/v1/documents/{id}/status` | Track processing status, stage, & progress % |
| `GET` | `/api/v1/documents` | List uploaded documents with pagination |
| `GET` | `/api/v1/documents/{id}/questions` | Retrieve extracted questions with filters |
| `GET` | `/api/v1/questions/{id}` | Retrieve individual question details |
| `PATCH` | `/api/v1/questions/{id}` | Human-in-the-loop review/correction endpoint |
| `GET` | `/api/v1/documents/{id}/answer-key` | Retrieve answer key mapping |
| `GET` | `/api/v1/documents/{id}/review-queue`| Retrieve questions flagged for human review |
| `POST` | `/api/v1/documents/{id}/associate` | Link related documents (e.g. Question Paper + Answer Key) |
| `POST` | `/api/v1/documents/{id}/reprocess` | Trigger re-extraction |
| `GET` | `/api/v1/documents/{id}/download` | Download original uploaded document |
| `GET` | `/api/v1/health` | Service health status |

---

## Postman Collection

Import `postman_collection.json` into Postman to explore and execute the complete API lifecycle. Pre-configured environment variables (`baseUrl`, `authToken`, `documentId`) are automatically populated.

---

## License & Evaluation Notice

This project was developed for the **Pragati Bharati Full Stack Developer Round 2 Engineering Assignment**. All rights reserved.

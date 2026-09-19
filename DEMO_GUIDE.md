# Demonstration & Evaluation Guide
## Pragati Bharati — Document Intelligence & Question Extraction Service

This guide provides step-by-step instructions for evaluating the **10 required demonstration scenarios** using:
1. **Automated Demo Runner** (`scripts/run_demo.py`) — one-click complete verification.
2. **Automated Test Suite** (`pytest tests/ -v`) — 100% passing test coverage.
3. **Interactive Swagger UI** (`http://localhost:8000/docs`).
4. **Postman Collection** (`postman_collection.json`).

---

## 1. Quick Verification (One-Click)

To run all 10 scenarios end-to-end and generate a live evidence report:

```bash
# Ensure virtual environment is active
.\.venv\Scripts\python scripts/run_demo.py
```

This script exercises all 10 scenarios and outputs:
- Real-time console logs showing each scenario's execution.
- `demo_evidence.json` containing the structured JSON results of all 10 scenarios.
- `samples/output/extracted_sample_1_questions.json` containing the final structured question schema.

---

## 2. Walkthrough of the 10 Evaluation Scenarios

### Scenario 1: Uploading a PDF Document
- **Input File**: `samples/input/sample_1_standard_exam.pdf`
- **What is Demonstrated**:
  - Uploading a digitally generated 2-page examination PDF.
  - Endpoint returns HTTP `202 Accepted` with `document_id` and `status_url`.
  - Asynchronous pipeline extracts questions and associates inline answer keys.
- **Verification API**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/documents/upload" \
    -H "Authorization: Bearer <TOKEN>" \
    -F "file=@samples/input/sample_1_standard_exam.pdf" \
    -F "document_type=QUESTION_PAPER"
  ```

---

### Scenario 2: Uploading an Image
- **Input File**: `samples/input/sample_2_question_paper.png`
- **What is Demonstrated**:
  - Uploading a visual question paper snapshot (PNG/JPEG).
  - Validation passes magic byte checks (`\x89PNG`).
  - Document status updates to `COMPLETED` with image metadata recorded.
- **Verification API**:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/documents/upload" \
    -H "Authorization: Bearer <TOKEN>" \
    -F "file=@samples/input/sample_2_question_paper.png"
  ```

---

### Scenario 3: Processing a Scanned / Low-Quality Document
- **Input File**: `samples/input/sample_3_scanned_low_quality.jpg`
- **What is Demonstrated**:
  - Processing degraded/low-resolution scans (small pixel dimensions, compression noise).
  - The system automatically detects image degradation, scales down confidence scores, and flags the item for human review (`status: NEEDS_REVIEW`, `review_reasons: ["LOW_RESOLUTION_IMAGE"]`).

---

### Scenario 4: Extracting Multiple Questions with Varied Numbering Formats
- **Input File**: `samples/input/sample_4_multi_questions.pdf`
- **What is Demonstrated**:
  - Extraction of 10+ questions from a single document.
  - Robust handling of varied numbering schemes: `1.`, `Q.2`, `Question 3:`, `4)`, `5.`, `Q.6`, `11(a)`.
  - Correct extraction of stems, options, and matching answer keys.

---

### Scenario 5: Handling a Question Spanning Multiple Pages
- **Input File**: `samples/input/sample_5_cross_page.pdf`
- **What is Demonstrated**:
  - Question 1 begins on Page 1 with options (A) and (B).
  - Options (C) and (D) continue onto Page 2.
  - The engine stitches them into a single question entity.
  - Provenance is preserved: `source_pages: [1, 2]`.
  - All 4 options are cleanly linked without duplicating the question stem.

---

### Scenario 6: Extracting Question Options & Complex Structures
- **Input File**: `samples/input/sample_6_rich_options.pdf`
- **What is Demonstrated**:
  - Examination question containing an embedded SQL table.
  - Options contain SQL query statements.
  - The engine sets `has_tables: True` and parses options `(A)`, `(B)`, `(C)`, `(D)` accurately.

---

### Scenario 7: Separate Answer Key Document Association
- **Input Files**:
  - `samples/input/sample_7_separate_question_paper.pdf` (Questions without answers)
  - `samples/input/sample_8_separate_answer_key.pdf` (Standalone answer key document)
- **What is Demonstrated**:
  - Uploading both documents independently.
  - Calling `POST /api/v1/documents/{question_paper_id}/associate` with `relation_type="ANSWER_KEY_FOR"`.
  - Cross-document answer alignment matches `sample_8` answers to `sample_7` questions.
  - Sets `association_method: "SEPARATE_DOCUMENT"`, extracts explanation (`"2x = 10 => x = 5"`), and confirms answers.

---

### Scenario 8: Showing Uncertain / Low-Confidence Extraction (Review Queue)
- **Input File**: `samples/input/sample_9_uncertain_low_confidence.pdf`
- **What is Demonstrated**:
  - Document with incomplete questions, missing options (only 1 option provided), and very short stems.
  - Automatically flagged with `status: "NEEDS_REVIEW"` and confidence $< 0.50$.
  - Viewable via the review queue endpoint:
    `GET /api/v1/documents/{id}/review-queue`.
  - Review reasons clearly populated: `["SHORT_QUESTION_STEM", "CRITICAL_MISSING_OPTIONS"]`.

---

### Scenario 9: Retrieving Final Structured Question Data
- **Output File**: `samples/output/extracted_sample_1_questions.json`
- **What is Demonstrated**:
  - Clean, platform-independent JSON schema:
    ```json
    {
      "id": "uuid",
      "document_id": "uuid",
      "question_number": "1",
      "question_text": "Which of the following data structures operates on a Last-In, First-Out (LIFO) principle?",
      "question_type": "MCQ",
      "options": [
        {"key": "A", "text": "Queue"},
        {"key": "B", "text": "Stack"},
        {"key": "C", "text": "Binary Tree"},
        {"key": "D", "text": "Hash Map"}
      ],
      "source_pages": [1],
      "confidence": 0.95,
      "status": "CONFIDENT",
      "has_tables": false,
      "has_images": false,
      "answer": {
        "raw_answer": "B",
        "normalized_answer": "B",
        "confidence": 0.9,
        "status": "CONFIRMED",
        "source_page": 2,
        "association_method": "INLINE_KEY_SECTION"
      }
    }
    ```

---

### Scenario 10: Handling Invalid or Unsupported Documents
- **Input File**: `samples/input/sample_10_malicious_disguised.pdf`
- **What is Demonstrated**:
  - Executable/malicious binary payload renamed to `.pdf`.
  - Storage service inspects magic bytes (file signature `%PDF-`).
  - Request is rejected with HTTP `400 Bad Request`:
    `"File signature (magic bytes) does not match any allowed format. File may be corrupted or disguised."`

---

## 3. Running the Automated Test Suite

```bash
.\.venv\Scripts\pytest -v
```

All 18 unit and integration tests pass, covering:
- Authentication & JWT security.
- Magic byte detection & path traversal security.
- Question extraction and option parsing.
- Cross-page question continuation.
- Answer key matching & separate document association.
- Review queue rules and confidence scoring.
- API endpoints and error handlers.

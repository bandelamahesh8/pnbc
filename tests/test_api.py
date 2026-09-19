import io
from pathlib import Path
import pytest
from app.core.database import get_sync_db
from app.services.document_service import document_service

SAMPLES_DIR = Path("samples/input")


@pytest.mark.asyncio
async def test_auth_workflow(client):
    # 1. Register new user
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "teacher@pragatibharati.edu",
            "password": "Password@123",
            "full_name": "Teacher One",
            "role": "reviewer"
        }
    )
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["email"] == "teacher@pragatibharati.edu"

    # 2. Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "teacher@pragatibharati.edu", "password": "Password@123"}
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Check me
    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "teacher@pragatibharati.edu"


@pytest.mark.asyncio
async def test_document_upload_and_extraction_workflow(client, auth_headers):
    pdf_path = SAMPLES_DIR / "sample_1_standard_exam.pdf"
    assert pdf_path.exists()

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    # 1. Upload document
    upload_resp = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("sample_1_standard_exam.pdf", io.BytesIO(file_bytes), "application/pdf")},
        data={"document_type": "QUESTION_PAPER"},
        headers=auth_headers
    )
    assert upload_resp.status_code == 202
    upload_data = upload_resp.json()
    doc_id = upload_data["document_id"]
    assert doc_id is not None

    # 2. Process document synchronously for test verification
    sync_db = get_sync_db()
    try:
        document_service.process_document(doc_id, sync_db)
    finally:
        sync_db.close()

    # 3. Check status
    status_resp = await client.get(f"/api/v1/documents/{doc_id}/status", headers=auth_headers)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] in ("COMPLETED", "NEEDS_REVIEW")
    assert status_data["question_count"] == 3
    assert status_data["has_answer_key"] is True

    # 4. Retrieve questions
    q_resp = await client.get(f"/api/v1/documents/{doc_id}/questions", headers=auth_headers)
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert q_data["total"] == 3
    first_q = q_data["items"][0]
    assert first_q["question_number"] == "1"
    assert len(first_q["options"]) == 4
    assert first_q["answer"] is not None
    assert first_q["answer"]["normalized_answer"] == "B"

    # 5. Retrieve individual question
    q_id = first_q["id"]
    single_q_resp = await client.get(f"/api/v1/questions/{q_id}", headers=auth_headers)
    assert single_q_resp.status_code == 200
    assert single_q_resp.json()["id"] == q_id

    # 6. Human-in-the-loop review/update question
    patch_resp = await client.patch(
        f"/api/v1/questions/{q_id}",
        json={"is_reviewed": True, "reviewer_notes": "Verified by reviewer"},
        headers=auth_headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_reviewed"] is True
    assert patch_resp.json()["reviewer_notes"] == "Verified by reviewer"

    # 7. Retrieve answer key
    ak_resp = await client.get(f"/api/v1/documents/{doc_id}/answer-key", headers=auth_headers)
    assert ak_resp.status_code == 200
    assert len(ak_resp.json()) == 3


@pytest.mark.asyncio
async def test_invalid_file_rejected(client, auth_headers):
    # Malicious file disguised as PDF
    invalid_bytes = b"MZ\x90\x00\x03\x00\x00\x00Not a real PDF"
    resp = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("malicious.pdf", io.BytesIO(invalid_bytes), "application/pdf")},
        headers=auth_headers
    )
    assert resp.status_code == 400
    assert "File signature (magic bytes) does not match" in resp.json()["message"]


@pytest.mark.asyncio
async def test_separate_answer_key_association(client, auth_headers):
    # Upload Question Paper
    with open(SAMPLES_DIR / "sample_7_separate_question_paper.pdf", "rb") as f:
        qp_bytes = f.read()
    qp_upload = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("qp.pdf", io.BytesIO(qp_bytes), "application/pdf")},
        headers=auth_headers
    )
    qp_id = qp_upload.json()["document_id"]

    # Upload Answer Key
    with open(SAMPLES_DIR / "sample_8_separate_answer_key.pdf", "rb") as f:
        ak_bytes = f.read()
    ak_upload = await client.post(
        "/api/v1/documents/upload",
        files={"file": ("ak.pdf", io.BytesIO(ak_bytes), "application/pdf")},
        headers=auth_headers
    )
    ak_id = ak_upload.json()["document_id"]

    # Process both
    sync_db = get_sync_db()
    try:
        document_service.process_document(qp_id, sync_db)
        document_service.process_document(ak_id, sync_db)
    finally:
        sync_db.close()

    # Associate Answer Key to Question Paper
    assoc_resp = await client.post(
        f"/api/v1/documents/{qp_id}/associate",
        json={"target_document_id": ak_id, "relation_type": "ANSWER_KEY_FOR"},
        headers=auth_headers
    )
    assert assoc_resp.status_code == 201

    # Verify questions now have the answers from the separate document!
    q_resp = await client.get(f"/api/v1/documents/{qp_id}/questions", headers=auth_headers)
    questions = q_resp.json()["items"]
    assert len(questions) == 2
    assert questions[0]["answer"] is not None
    assert questions[0]["answer"]["normalized_answer"] == "B"
    assert questions[0]["answer"]["association_method"] == "SEPARATE_DOCUMENT"


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("HEALTHY", "DEGRADED")
    assert "components" in data

import math
from typing import List, Optional
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppException, ForbiddenException, NotFoundException
from app.models.answer_key import AnswerKey
from app.models.document import Document
from app.models.document_relation import DocumentRelation
from app.models.question import Question
from app.models.user import User
from app.schemas.answer_key import AnswerKeyOut
from app.schemas.common import (
    DocumentRelationType,
    DocumentStatus,
    ExtractionStatus,
    PaginatedResponse,
    QuestionType,
)
from app.schemas.document import (
    DocumentOut,
    DocumentRelationCreate,
    DocumentRelationOut,
    DocumentReviewQueueResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
)
from app.schemas.question import QuestionOut, QuestionReviewItem
from app.services.storage import storage_service
from app.workers.tasks import dispatch_document_processing

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF or Image file (JPEG, PNG, WebP)"),
    document_set_id: Optional[str] = Form(None, description="Optional ID to group related documents"),
    document_type: Optional[str] = Form("QUESTION_PAPER", description="QUESTION_PAPER, ANSWER_KEY, or COMBINED"),
    related_document_id: Optional[str] = Form(None, description="ID of a document to associate with (e.g. Question Paper)"),
    relation_type: Optional[DocumentRelationType] = Form(DocumentRelationType.ANSWER_KEY_FOR),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a PDF or image document for asynchronous document intelligence and question extraction.
    Returns HTTP 202 Accepted immediately with status tracking details.
    """
    # Validate and save file securely
    original_name, storage_path, mime_type, file_size, file_hash = await storage_service.validate_and_save(file)

    doc = Document(
        user_id=current_user.id,
        original_filename=original_name,
        storage_path=storage_path,
        mime_type=mime_type,
        file_size_bytes=file_size,
        file_hash=file_hash,
        status=DocumentStatus.PENDING.value,
        stage="UPLOADED",
        progress_percent=0,
        document_set_id=document_set_id,
        document_type=document_type or "QUESTION_PAPER",
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Link related document if provided
    if related_document_id:
        target_doc = await db.get(Document, related_document_id)
        if target_doc:
            rel = DocumentRelation(
                source_document_id=doc.id,
                target_document_id=related_document_id,
                relation_type=relation_type.value,
            )
            db.add(rel)
            await db.commit()

    # Dispatch asynchronous background task
    dispatch_document_processing(doc.id, background_tasks)

    status_url = f"{settings.API_V1_STR}/documents/{doc.id}/status"
    return DocumentUploadResponse(
        document_id=doc.id,
        original_filename=doc.original_filename,
        status=DocumentStatus(doc.status),
        message="Document uploaded successfully. Processing started asynchronously.",
        status_url=status_url,
        document_set_id=doc.document_set_id,
    )


@router.get("", response_model=PaginatedResponse[DocumentOut])
async def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[DocumentStatus] = Query(None, alias="status"),
    document_set_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List documents uploaded by the current user."""
    query = select(Document)
    if current_user.role != "admin":
        query = query.where(Document.user_id == current_user.id)
    if status_filter:
        query = query.where(Document.status == status_filter.value)
    if document_set_id:
        query = query.where(Document.document_set_id == document_set_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar_one()

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
    items_res = await db.execute(query)
    items = items_res.scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse[DocumentOut](
        items=[DocumentOut.model_validate(d) for d in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the real-time processing status, progress percentage, and stage of a document."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise NotFoundException(f"Document with ID '{document_id}' not found.")
    if current_user.role != "admin" and doc.user_id != current_user.id:
        raise ForbiddenException("You are not authorized to access this document.")

    # Calculate question counts
    q_stats = await db.execute(
        select(
            func.count(Question.id),
            func.count(func.nullif(Question.status != "CONFIDENT", True)),
            func.count(func.nullif(Question.status != "NEEDS_REVIEW", True)),
        ).where(Question.document_id == document_id)
    )
    total_q, confident_q, review_q = q_stats.one()

    # Check if answer key exists
    ak_check = await db.execute(
        select(func.count(AnswerKey.id))
        .join(Question, AnswerKey.question_id == Question.id)
        .where(Question.document_id == document_id)
    )
    has_answer_key = (ak_check.scalar_one() or 0) > 0

    return DocumentStatusResponse(
        id=doc.id,
        original_filename=doc.original_filename,
        status=DocumentStatus(doc.status),
        stage=doc.stage,
        progress_percent=doc.progress_percent,
        page_count=doc.page_count,
        question_count=total_q or 0,
        confident_count=confident_q or 0,
        needs_review_count=review_q or 0,
        has_answer_key=has_answer_key,
        error_message=doc.error_message,
        updated_at=doc.updated_at,
    )


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document_details(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full metadata of a document."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise NotFoundException(f"Document '{document_id}' not found.")
    if current_user.role != "admin" and doc.user_id != current_user.id:
        raise ForbiddenException("Unauthorized.")
    return DocumentOut.model_validate(doc)


@router.get("/{document_id}/questions", response_model=PaginatedResponse[QuestionOut])
async def get_document_questions(
    document_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    source_page: Optional[int] = Query(None, description="Filter by original source page number"),
    question_type: Optional[QuestionType] = Query(None, description="Filter by question type"),
    status_filter: Optional[ExtractionStatus] = Query(None, alias="status", description="Filter by extraction status"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all structured questions extracted from a document.
    Supports filtering by page number, question type, confidence threshold, and review status.
    """
    doc = await db.get(Document, document_id)
    if not doc:
        raise NotFoundException(f"Document '{document_id}' not found.")
    if current_user.role != "admin" and doc.user_id != current_user.id:
        raise ForbiddenException("Unauthorized.")

    query = select(Question).where(Question.document_id == document_id).options(selectinload(Question.answer))

    if question_type:
        query = query.where(Question.question_type == question_type.value)
    if status_filter:
        query = query.where(Question.status == status_filter.value)
    if min_confidence is not None:
        query = query.where(Question.confidence >= min_confidence)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar_one()

    # Sort & Paginate
    offset = (page - 1) * page_size
    query = query.order_by(Question.created_at.asc()).offset(offset).limit(page_size)
    items_res = await db.execute(query)
    raw_questions = items_res.scalars().all()

    # Filter by source page in python if specified (since source_pages is a JSON array)
    if source_page is not None:
        raw_questions = [q for q in raw_questions if source_page in (q.source_pages or [])]
        total = len(raw_questions)

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse[QuestionOut](
        items=[QuestionOut.model_validate(q) for q in raw_questions],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{document_id}/answer-key", response_model=List[AnswerKeyOut])
async def get_document_answer_key(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all answer keys identified and associated with questions in this document."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise NotFoundException(f"Document '{document_id}' not found.")
    if current_user.role != "admin" and doc.user_id != current_user.id:
        raise ForbiddenException("Unauthorized.")

    stmt = (
        select(AnswerKey)
        .join(Question, AnswerKey.question_id == Question.id)
        .where(Question.document_id == document_id)
        .order_by(AnswerKey.created_at.asc())
    )
    result = await db.execute(stmt)
    answers = result.scalars().all()
    return [AnswerKeyOut.model_validate(a) for a in answers]


@router.get("/{document_id}/review-queue", response_model=DocumentReviewQueueResponse)
async def get_document_review_queue(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all questions from this document that were flagged for human review
    (due to low confidence, missing options, cross-page split uncertainty, or unmatched answers).
    """
    doc = await db.get(Document, document_id)
    if not doc:
        raise NotFoundException(f"Document '{document_id}' not found.")
    if current_user.role != "admin" and doc.user_id != current_user.id:
        raise ForbiddenException("Unauthorized.")

    # Fetch questions where status is NEEDS_REVIEW or confidence < 0.70
    stmt = (
        select(Question)
        .where(
            Question.document_id == document_id,
            (Question.status == ExtractionStatus.NEEDS_REVIEW.value) | (Question.confidence < 0.70)
        )
        .options(selectinload(Question.answer))
        .order_by(Question.confidence.asc())
    )
    result = await db.execute(stmt)
    review_questions = result.scalars().all()

    total_q_stmt = select(func.count(Question.id)).where(Question.document_id == document_id)
    total_q_res = await db.execute(total_q_stmt)
    total_q = total_q_res.scalar_one()

    items = []
    for q in review_questions:
        has_unmatched = (q.answer is None) or (q.answer.status == "NOT_FOUND")
        items.append(
            QuestionReviewItem(
                id=q.id,
                document_id=q.document_id,
                question_number=q.question_number,
                question_text=q.question_text,
                question_type=QuestionType(q.question_type),
                confidence=q.confidence,
                status=ExtractionStatus(q.status),
                review_reasons=q.review_reasons or [],
                source_pages=q.source_pages or [],
                has_unmatched_answer=has_unmatched,
                is_reviewed=q.is_reviewed,
            )
        )

    return DocumentReviewQueueResponse(
        document_id=document_id,
        total_questions=total_q,
        needs_review_count=len(items),
        items=items,
    )


@router.post("/{document_id}/associate", response_model=DocumentRelationOut, status_code=status.HTTP_201_CREATED)
async def associate_document(
    document_id: str,
    relation_in: DocumentRelationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Associate a related document (e.g. link an Answer Key PDF with a Question Paper PDF).
    Triggers cross-document answer alignment to match the answer keys to the question paper.
    """
    source_doc = await db.get(Document, document_id)
    target_doc = await db.get(Document, relation_in.target_document_id)

    if not source_doc or not target_doc:
        raise NotFoundException("One or both documents not found.")
    if current_user.role != "admin" and (source_doc.user_id != current_user.id or target_doc.user_id != current_user.id):
        raise ForbiddenException("Unauthorized to modify these documents.")

    # Use sync engine inside service for document association and answer realignment
    from app.core.database import get_sync_db
    from app.services.document_service import document_service

    sync_db = get_sync_db()
    try:
        rel = document_service.associate_and_realign_answers(
            source_doc_id=document_id,
            answer_key_doc_id=relation_in.target_document_id,
            relation_type=relation_in.relation_type.value,
            db=sync_db
        )
        return DocumentRelationOut(
            id=rel.id,
            source_document_id=rel.source_document_id,
            target_document_id=rel.target_document_id,
            relation_type=DocumentRelationType(rel.relation_type),
            created_at=rel.created_at,
        )
    finally:
        sync_db.close()


@router.post("/{document_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger re-extraction and processing of an existing document."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise NotFoundException(f"Document '{document_id}' not found.")
    if current_user.role != "admin" and doc.user_id != current_user.id:
        raise ForbiddenException("Unauthorized.")

    doc.status = DocumentStatus.PENDING.value
    doc.stage = "REPROCESSING_QUEUED"
    doc.progress_percent = 0
    doc.error_message = None
    await db.commit()

    dispatch_document_processing(doc.id, background_tasks)
    return {"message": "Document reprocessing queued.", "document_id": doc.id}


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download the original uploaded document file."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise NotFoundException(f"Document '{document_id}' not found.")
    if current_user.role != "admin" and doc.user_id != current_user.id:
        raise ForbiddenException("Unauthorized.")

    return FileResponse(
        path=doc.storage_path,
        filename=doc.original_filename,
        media_type=doc.mime_type
    )

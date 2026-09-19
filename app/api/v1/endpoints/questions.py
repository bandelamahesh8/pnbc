import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenException, NotFoundException
from app.models.document import Document
from app.models.question import Question
from app.models.user import User
from app.schemas.common import ExtractionStatus, PaginatedResponse, QuestionType
from app.schemas.question import QuestionOut, QuestionReviewItem, QuestionUpdate

router = APIRouter(prefix="/questions", tags=["Questions"])


@router.get("/review-queue", response_model=PaginatedResponse[QuestionReviewItem])
async def get_global_review_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_reviewed: Optional[bool] = Query(False, description="Filter by reviewed status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve questions across all documents that require human review
    (low confidence, missing options, cross-page split uncertainty, or unmatched answers).
    """
    query = (
        select(Question)
        .join(Document, Question.document_id == Document.id)
        .where(
            (Question.status == ExtractionStatus.NEEDS_REVIEW.value) | (Question.confidence < 0.70)
        )
        .options(selectinload(Question.answer))
    )

    if current_user.role != "admin":
        query = query.where(Document.user_id == current_user.id)
    if is_reviewed is not None:
        query = query.where(Question.is_reviewed == is_reviewed)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_res = await db.execute(count_query)
    total = total_res.scalar_one()

    # Paginate
    offset = (page - 1) * page_size
    query = query.order_by(Question.confidence.asc()).offset(offset).limit(page_size)
    items_res = await db.execute(query)
    questions = items_res.scalars().all()

    items = []
    for q in questions:
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

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedResponse[QuestionReviewItem](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{question_id}", response_model=QuestionOut)
async def get_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve detailed information for an individual question, including its options and answer key."""
    stmt = (
        select(Question)
        .where(Question.id == question_id)
        .options(selectinload(Question.answer), selectinload(Question.document))
    )
    result = await db.execute(stmt)
    q = result.scalar_one_or_none()

    if not q:
        raise NotFoundException(f"Question with ID '{question_id}' not found.")
    if current_user.role != "admin" and q.document.user_id != current_user.id:
        raise ForbiddenException("Unauthorized to access this question.")

    return QuestionOut.model_validate(q)


@router.patch("/{question_id}", response_model=QuestionOut)
async def update_or_review_question(
    question_id: str,
    question_update: QuestionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Human-in-the-loop review and correction endpoint.
    Allows reviewers to edit question text, options, question numbers, or approve questions.
    """
    stmt = (
        select(Question)
        .where(Question.id == question_id)
        .options(selectinload(Question.answer), selectinload(Question.document))
    )
    result = await db.execute(stmt)
    q = result.scalar_one_or_none()

    if not q:
        raise NotFoundException(f"Question with ID '{question_id}' not found.")
    if current_user.role != "admin" and q.document.user_id != current_user.id:
        raise ForbiddenException("Unauthorized.")

    # Apply updates
    if question_update.question_number is not None:
        q.question_number = question_update.question_number
    if question_update.question_text is not None:
        q.question_text = question_update.question_text
    if question_update.question_type is not None:
        q.question_type = question_update.question_type.value
    if question_update.options is not None:
        q.options = [opt.model_dump() for opt in question_update.options]
    if question_update.confidence is not None:
        q.confidence = question_update.confidence
    if question_update.status is not None:
        q.status = question_update.status.value
    if question_update.is_reviewed is not None:
        q.is_reviewed = question_update.is_reviewed
        if question_update.is_reviewed and question_update.status is None:
            # Mark as confident once human-reviewed
            q.status = ExtractionStatus.CONFIDENT.value
    if question_update.reviewer_notes is not None:
        q.reviewer_notes = question_update.reviewer_notes

    await db.commit()
    await db.refresh(q)
    return QuestionOut.model_validate(q)

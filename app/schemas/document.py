from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import DocumentRelationType, DocumentStatus
from app.schemas.question import QuestionOut, QuestionReviewItem


class DocumentBase(BaseModel):
    original_filename: str
    mime_type: str
    file_size_bytes: int
    document_type: str = "QUESTION_PAPER"
    document_set_id: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    original_filename: str
    status: DocumentStatus
    message: str
    status_url: str
    document_set_id: Optional[str] = None


class DocumentStatusResponse(BaseModel):
    id: str
    original_filename: str
    status: DocumentStatus
    stage: str
    progress_percent: int
    page_count: Optional[int] = None
    question_count: int = 0
    confident_count: int = 0
    needs_review_count: int = 0
    has_answer_key: bool = False
    error_message: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentOut(DocumentBase):
    id: str
    user_id: str
    file_hash: str
    page_count: Optional[int] = None
    status: DocumentStatus
    stage: str
    progress_percent: int
    error_message: Optional[str] = None
    extraction_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentRelationCreate(BaseModel):
    target_document_id: str = Field(..., description="ID of the related document (e.g. Answer Key)")
    relation_type: DocumentRelationType = Field(
        DocumentRelationType.ANSWER_KEY_FOR,
        description="Type of relationship: ANSWER_KEY_FOR, SUPPLEMENT_TO, etc."
    )


class DocumentRelationOut(BaseModel):
    id: str
    source_document_id: str
    target_document_id: str
    relation_type: DocumentRelationType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentReviewQueueResponse(BaseModel):
    document_id: str
    total_questions: int
    needs_review_count: int
    items: List[QuestionReviewItem]

    model_config = ConfigDict(from_attributes=True)

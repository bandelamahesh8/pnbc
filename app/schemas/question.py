from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import ExtractionStatus, QuestionType
from app.schemas.answer_key import AnswerKeyBase, AnswerKeyOut


class OptionItem(BaseModel):
    key: str = Field(..., description="Option identifier, e.g. 'A', 'B', '1', 'i'")
    text: str = Field(..., description="Option text or statement")

    model_config = ConfigDict(from_attributes=True)


class QuestionBase(BaseModel):
    question_number: Optional[str] = Field(None, description="Question number/identifier, e.g. '1', 'Q.2'")
    question_text: str = Field(..., description="Full text of the question")
    question_type: QuestionType = Field(QuestionType.MCQ, description="Categorized question type")
    options: List[OptionItem] = Field(default_factory=list, description="List of options for MCQ/Multi-select")
    source_pages: List[int] = Field(..., description="Original page number(s) where question was found")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Extraction confidence score (0.0 - 1.0)")
    status: ExtractionStatus = Field(ExtractionStatus.CONFIDENT, description="Extraction status")
    review_reasons: List[str] = Field(default_factory=list, description="Reasons flagged for human review")
    has_tables: bool = Field(False, description="Whether question contains tabular data")
    has_images: bool = Field(False, description="Whether question contains embedded images/diagrams")
    metadata_info: Dict[str, Any] = Field(default_factory=dict, description="Additional structural metadata")


class QuestionCreate(QuestionBase):
    document_id: str
    answer: Optional[AnswerKeyBase] = None


class QuestionUpdate(BaseModel):
    question_number: Optional[str] = None
    question_text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    options: Optional[List[OptionItem]] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    status: Optional[ExtractionStatus] = None
    is_reviewed: Optional[bool] = None
    reviewer_notes: Optional[str] = None


class QuestionOut(QuestionBase):
    id: str
    document_id: str
    is_reviewed: bool
    reviewer_notes: Optional[str] = None
    answer: Optional[AnswerKeyOut] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionReviewItem(BaseModel):
    id: str
    document_id: str
    question_number: Optional[str]
    question_text: str
    question_type: QuestionType
    confidence: float
    status: ExtractionStatus
    review_reasons: List[str]
    source_pages: List[int]
    has_unmatched_answer: bool
    is_reviewed: bool

    model_config = ConfigDict(from_attributes=True)

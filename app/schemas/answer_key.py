from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import AnswerStatus


class AnswerKeyBase(BaseModel):
    raw_answer: str = Field(..., description="Raw answer text detected in source document")
    normalized_answer: str = Field(..., description="Standardized answer representation, e.g. 'A', 'True'")
    explanation: Optional[str] = Field(None, description="Explanation or solution rationale if present")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence score of answer detection")
    status: AnswerStatus = Field(AnswerStatus.CONFIRMED, description="Status of the answer mapping")
    source_page: Optional[int] = Field(None, description="Page where the answer was found")
    association_method: str = Field(
        "INLINE_KEY_SECTION",
        description="Method used: INLINE_KEY_SECTION, SEPARATE_DOCUMENT, EMBEDDED, etc."
    )
    warnings: List[str] = Field(default_factory=list, description="Any warnings or uncertainties")


class AnswerKeyCreate(AnswerKeyBase):
    question_id: str
    source_document_id: Optional[str] = None


class AnswerKeyUpdate(BaseModel):
    normalized_answer: Optional[str] = None
    raw_answer: Optional[str] = None
    explanation: Optional[str] = None
    status: Optional[AnswerStatus] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class AnswerKeyOut(AnswerKeyBase):
    id: str
    question_id: str
    source_document_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import AnswerStatus, ExtractionStatus, QuestionType
from app.schemas.question import OptionItem


class ExtractedAnswerKey(BaseModel):
    question_number: Optional[str] = None
    raw_answer: str
    normalized_answer: str
    explanation: Optional[str] = None
    source_page: Optional[int] = None
    confidence: float = 1.0
    status: AnswerStatus = AnswerStatus.CONFIRMED
    association_method: str = "INLINE_KEY_SECTION"
    warnings: List[str] = Field(default_factory=list)


class ExtractedQuestion(BaseModel):
    question_number: Optional[str] = None
    question_text: str
    question_type: QuestionType = QuestionType.MCQ
    options: List[OptionItem] = Field(default_factory=list)
    source_pages: List[int] = Field(default_factory=list)
    confidence: float = 1.0
    status: ExtractionStatus = ExtractionStatus.CONFIDENT
    review_reasons: List[str] = Field(default_factory=list)
    has_tables: bool = False
    has_images: bool = False
    metadata_info: Dict[str, Any] = Field(default_factory=dict)
    answer: Optional[ExtractedAnswerKey] = None


class ExtractionResult(BaseModel):
    questions: List[ExtractedQuestion] = Field(default_factory=list)
    standalone_answers: List[ExtractedAnswerKey] = Field(default_factory=list)
    page_count: int = 1
    engine_used: str = "unknown"
    document_type: str = "QUESTION_PAPER"
    warnings: List[str] = Field(default_factory=list)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_bytes: bytes, mime_type: str, filename: str) -> ExtractionResult:
        """Extract structured questions and answer keys from document bytes."""
        pass

from enum import Enum
from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class QuestionType(str, Enum):
    MCQ = "MCQ"
    MULTI_SELECT = "MULTI_SELECT"
    TRUE_FALSE = "TRUE_FALSE"
    FILL_IN_THE_BLANK = "FILL_IN_THE_BLANK"
    SHORT_ANSWER = "SHORT_ANSWER"
    DESCRIPTIVE = "DESCRIPTIVE"


class ExtractionStatus(str, Enum):
    CONFIDENT = "CONFIDENT"
    PARTIALLY_EXTRACTED = "PARTIALLY_EXTRACTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class AnswerStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    INFERRED = "INFERRED"
    UNCERTAIN = "UNCERTAIN"
    NOT_FOUND = "NOT_FOUND"


class DocumentRelationType(str, Enum):
    ANSWER_KEY_FOR = "ANSWER_KEY_FOR"
    SUPPLEMENT_TO = "SUPPLEMENT_TO"
    QUESTION_PAPER_FOR = "QUESTION_PAPER_FOR"


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)

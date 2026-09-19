from typing import List, Optional
from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class Question(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "questions"

    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(
        String(50), default="MCQ", nullable=False, index=True
    )  # MCQ, MULTI_SELECT, TRUE_FALSE, FILL_IN_THE_BLANK, SHORT_ANSWER, DESCRIPTIVE
    options: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)
    source_pages: Mapped[List[int]] = mapped_column(JSON, default=list, nullable=False)
    
    # Confidence and Review Queue
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(50), default="CONFIDENT", nullable=False, index=True
    )  # CONFIDENT, PARTIALLY_EXTRACTED, NEEDS_REVIEW
    review_reasons: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)
    is_reviewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Document Elements
    has_tables: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_images: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_info: Mapped[Optional[dict]] = mapped_column(JSON, default=dict, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="questions")
    answer = relationship(
        "AnswerKey", back_populates="question", uselist=False, cascade="all, delete-orphan"
    )

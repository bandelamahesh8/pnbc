from typing import Optional
from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class AnswerKey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "answer_keys"

    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    source_document_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    raw_answer: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_answer: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="CONFIRMED", nullable=False
    )  # CONFIRMED, INFERRED, UNCERTAIN, NOT_FOUND
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    association_method: Mapped[str] = mapped_column(
        String(100), default="INLINE_KEY_SECTION", nullable=False
    )
    warnings: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)

    question = relationship("Question", back_populates="answer")
    source_document = relationship("Document", foreign_keys=[source_document_id])

from typing import List, Optional
from sqlalchemy import BigInteger, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class Document(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "documents"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PENDING", index=True
    )  # PENDING, PROCESSING, COMPLETED, FAILED, NEEDS_REVIEW
    stage: Mapped[str] = mapped_column(
        String(100), nullable=False, default="UPLOADED"
    )  # UPLOADED, PARSING_FILE, EXTRACTING_QUESTIONS, ASSOCIATING_ANSWERS, VALIDATING, DONE, ERROR
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Document Grouping & Classification
    document_set_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)
    document_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="QUESTION_PAPER"
    )  # QUESTION_PAPER, ANSWER_KEY, COMBINED, SUPPLEMENT
    extraction_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="documents")
    questions = relationship("Question", back_populates="document", cascade="all, delete-orphan")
    relations_as_source = relationship(
        "DocumentRelation",
        foreign_keys="DocumentRelation.source_document_id",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
    relations_as_target = relationship(
        "DocumentRelation",
        foreign_keys="DocumentRelation.target_document_id",
        back_populates="target_document",
        cascade="all, delete-orphan",
    )

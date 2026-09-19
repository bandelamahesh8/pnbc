from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin, UUIDMixin


class DocumentRelation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "document_relations"

    source_document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ANSWER_KEY_FOR"
    )  # ANSWER_KEY_FOR, SUPPLEMENT_TO, QUESTION_PAPER_FOR

    source_document = relationship(
        "Document", foreign_keys=[source_document_id], back_populates="relations_as_source"
    )
    target_document = relationship(
        "Document", foreign_keys=[target_document_id], back_populates="relations_as_target"
    )

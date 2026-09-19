import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.answer_key import AnswerKey
from app.models.document import Document
from app.models.document_relation import DocumentRelation
from app.models.question import Question
from app.schemas.common import AnswerStatus, DocumentRelationType, DocumentStatus, ExtractionStatus
from app.services.extraction.answer_matcher import answer_matcher
from app.services.extraction.gemini_extractor import GeminiExtractor
from app.services.extraction.rule_extractor import rule_extractor
from app.services.extraction.validator import extraction_validator
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self):
        self.gemini_extractor = GeminiExtractor()
        self.rule_extractor = rule_extractor

    def process_document(self, document_id: str, db: Session) -> Document:
        """
        Main asynchronous processing pipeline for an uploaded document.
        Executes parsing, question extraction, answer key association, and quality validation.
        """
        doc = db.get(Document, document_id)
        if not doc:
            logger.error(f"Document {document_id} not found for processing.")
            return None

        try:
            # Stage 1: Reading file
            doc.status = DocumentStatus.PROCESSING.value
            doc.stage = "READING_FILE"
            doc.progress_percent = 15
            db.commit()

            file_bytes = storage_service.get_file_bytes(doc.storage_path)

            # Stage 2: Extraction Strategy Selection
            doc.stage = "EXTRACTING_QUESTIONS"
            doc.progress_percent = 35
            db.commit()

            extraction_result = None
            if self.gemini_extractor.is_available():
                try:
                    logger.info(f"Using Gemini Multimodal extractor for doc {document_id}")
                    extraction_result = self.gemini_extractor.extract(
                        file_bytes=file_bytes,
                        mime_type=doc.mime_type,
                        filename=doc.original_filename
                    )
                except Exception as ex:
                    logger.warning(
                        f"Gemini extractor failed ({ex}). Falling back to RuleBasedExtractor."
                    )

            if not extraction_result:
                logger.info(f"Using Rule-Based extractor for doc {document_id}")
                extraction_result = self.rule_extractor.extract(
                    file_bytes=file_bytes,
                    mime_type=doc.mime_type,
                    filename=doc.original_filename
                )

            # Stage 3: Associating Answer Keys
            doc.stage = "ASSOCIATING_ANSWERS"
            doc.progress_percent = 65
            db.commit()

            # Check if standalone answers were found in this document
            questions = extraction_result.questions
            standalone_answers = extraction_result.standalone_answers

            # Also check if an associated Answer Key document was already linked
            stmt = select(DocumentRelation).where(
                DocumentRelation.source_document_id == document_id,
                DocumentRelation.relation_type == DocumentRelationType.ANSWER_KEY_FOR.value
            )
            relations = db.execute(stmt).scalars().all()
            for rel in relations:
                # Load questions from the target answer key document
                ak_doc = db.get(Document, rel.target_document_id)
                if ak_doc:
                    target_questions = db.execute(
                        select(Question).where(Question.document_id == ak_doc.id)
                    ).scalars().all()
                    for tq in target_questions:
                        if tq.answer:
                            from app.services.extraction.base import ExtractedAnswerKey
                            standalone_answers.append(
                                ExtractedAnswerKey(
                                    question_number=tq.question_number,
                                    raw_answer=tq.answer.raw_answer,
                                    normalized_answer=tq.answer.normalized_answer,
                                    explanation=tq.answer.explanation,
                                    source_page=tq.answer.source_page,
                                    confidence=tq.answer.confidence,
                                    status=tq.answer.status,
                                    association_method="SEPARATE_DOCUMENT"
                                )
                            )

            if standalone_answers:
                questions, _ = answer_matcher.associate_answers(
                    questions=questions,
                    answer_keys=standalone_answers,
                    source_document_id=document_id,
                    association_method="INLINE_KEY_SECTION"
                )

            # Stage 4: Confidence Scoring & Review Queue Validation
            doc.stage = "VALIDATING"
            doc.progress_percent = 85
            db.commit()

            questions, summary = extraction_validator.validate_and_score(
                questions=questions,
                document_warnings=extraction_result.warnings
            )

            # Stage 5: Persisting Questions & Answers to DB
            # Remove any existing questions (for idempotent reprocessing)
            existing_questions = db.execute(
                select(Question).where(Question.document_id == document_id)
            ).scalars().all()
            for eq in existing_questions:
                db.delete(eq)
            db.flush()

            for q_data in questions:
                q_model = Question(
                    document_id=document_id,
                    question_number=q_data.question_number,
                    question_text=q_data.question_text,
                    question_type=q_data.question_type.value,
                    options=[{"key": opt.key, "text": opt.text} for opt in q_data.options],
                    source_pages=q_data.source_pages,
                    confidence=q_data.confidence,
                    status=q_data.status.value,
                    review_reasons=q_data.review_reasons,
                    has_tables=q_data.has_tables,
                    has_images=q_data.has_images,
                    metadata_info=q_data.metadata_info,
                )
                db.add(q_model)
                db.flush()

                if q_data.answer and q_data.answer.status != AnswerStatus.NOT_FOUND:
                    ak_model = AnswerKey(
                        question_id=q_model.id,
                        source_document_id=document_id,
                        raw_answer=q_data.answer.raw_answer,
                        normalized_answer=q_data.answer.normalized_answer,
                        explanation=q_data.answer.explanation,
                        confidence=q_data.answer.confidence,
                        status=q_data.answer.status.value,
                        source_page=q_data.answer.source_page,
                        association_method=q_data.answer.association_method,
                        warnings=q_data.answer.warnings,
                    )
                    db.add(ak_model)

            # Stage 6: Completion
            doc.page_count = extraction_result.page_count
            doc.stage = "DONE"
            doc.progress_percent = 100
            doc.document_type = extraction_result.document_type

            if summary["needs_review_count"] > 0:
                doc.status = DocumentStatus.NEEDS_REVIEW.value
            else:
                doc.status = DocumentStatus.COMPLETED.value

            doc.extraction_metadata = {
                "engine_used": extraction_result.engine_used,
                "summary": summary,
                "warnings": extraction_result.warnings,
            }
            db.commit()
            db.refresh(doc)
            logger.info(f"Successfully processed document {document_id} with status {doc.status}")
            return doc

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}", exc_info=True)
            doc.status = DocumentStatus.FAILED.value
            doc.stage = "ERROR"
            doc.error_message = str(e)
            db.commit()
            raise

    def associate_and_realign_answers(
        self,
        source_doc_id: str,
        answer_key_doc_id: str,
        relation_type: str,
        db: Session
    ) -> DocumentRelation:
        """
        Creates a document relationship and immediately aligns answer keys
        from the answer key document to the source question paper.
        """
        source_doc = db.get(Document, source_doc_id)
        target_doc = db.get(Document, answer_key_doc_id)

        if not source_doc or not target_doc:
            raise ValueError("Both source and target documents must exist.")

        # Create relation
        relation = DocumentRelation(
            source_document_id=source_doc_id,
            target_document_id=answer_key_doc_id,
            relation_type=relation_type,
        )
        db.add(relation)
        db.commit()

        if relation_type == DocumentRelationType.ANSWER_KEY_FOR.value:
            # Realign answers from target_doc to source_doc
            source_questions = db.execute(
                select(Question).where(Question.document_id == source_doc_id)
            ).scalars().all()

            target_questions = db.execute(
                select(Question).where(Question.document_id == answer_key_doc_id)
            ).scalars().all()

            # Build list of answer keys from target
            from app.services.extraction.base import ExtractedAnswerKey, ExtractedQuestion
            from app.schemas.question import OptionItem

            target_answers: List[ExtractedAnswerKey] = []
            for tq in target_questions:
                ans_text = tq.question_text
                # If target has an answer record
                if tq.answer:
                    ans_text = tq.answer.normalized_answer
                target_answers.append(
                    ExtractedAnswerKey(
                        question_number=tq.question_number,
                        raw_answer=ans_text,
                        normalized_answer=ans_text,
                        source_page=tq.source_pages[0] if tq.source_pages else 1,
                        confidence=0.90,
                        status=AnswerStatus.CONFIRMED,
                        association_method="SEPARATE_DOCUMENT"
                    )
                )

            # Map source_questions to ExtractedQuestion format
            eq_list = []
            for sq in source_questions:
                eq_list.append(
                    ExtractedQuestion(
                        question_number=sq.question_number,
                        question_text=sq.question_text,
                        options=[OptionItem(key=o["key"], text=o["text"]) for o in (sq.options or [])],
                        source_pages=sq.source_pages,
                        confidence=sq.confidence,
                    )
                )

            aligned_questions, _ = answer_matcher.associate_answers(
                questions=eq_list,
                answer_keys=target_answers,
                source_document_id=answer_key_doc_id,
                association_method="SEPARATE_DOCUMENT"
            )

            # Update DB records
            for idx, sq in enumerate(source_questions):
                aligned_q = aligned_questions[idx]
                if aligned_q.answer and aligned_q.answer.status != AnswerStatus.NOT_FOUND:
                    if sq.answer:
                        sq.answer.raw_answer = aligned_q.answer.raw_answer
                        sq.answer.normalized_answer = aligned_q.answer.normalized_answer
                        sq.answer.status = aligned_q.answer.status.value
                        sq.answer.confidence = aligned_q.answer.confidence
                        sq.answer.association_method = "SEPARATE_DOCUMENT"
                        sq.answer.source_document_id = answer_key_doc_id
                    else:
                        new_ak = AnswerKey(
                            question_id=sq.id,
                            source_document_id=answer_key_doc_id,
                            raw_answer=aligned_q.answer.raw_answer,
                            normalized_answer=aligned_q.answer.normalized_answer,
                            confidence=aligned_q.answer.confidence,
                            status=aligned_q.answer.status.value,
                            source_page=aligned_q.answer.source_page,
                            association_method="SEPARATE_DOCUMENT"
                        )
                        db.add(new_ak)

            db.commit()

        return relation


document_service = DocumentService()

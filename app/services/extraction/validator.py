from typing import List, Tuple
from app.core.config import settings
from app.schemas.common import AnswerStatus, ExtractionStatus, QuestionType
from app.services.extraction.base import ExtractedQuestion


class ExtractionValidator:
    """
    Validates questions against quality rules and assigns final confidence scores
    and review queue statuses.
    """

    def validate_and_score(
        self,
        questions: List[ExtractedQuestion],
        document_warnings: List[str]
    ) -> Tuple[List[ExtractedQuestion], dict]:
        """
        Calculates confidence, determines status (CONFIDENT, PARTIALLY_EXTRACTED, NEEDS_REVIEW),
        and collects summary metrics.
        """
        confident_count = 0
        partially_extracted_count = 0
        needs_review_count = 0

        for q in questions:
            reasons = list(q.review_reasons)
            score = q.confidence

            # Rule 1: Question Stem Quality
            if len(q.question_text.strip()) < 15:
                score = min(score, 0.60)
                if "SHORT_QUESTION_STEM" not in reasons:
                    reasons.append("SHORT_QUESTION_STEM")

            # Rule 2: MCQ Option Completeness
            if q.question_type in (QuestionType.MCQ, QuestionType.MULTI_SELECT):
                if len(q.options) < 2:
                    score = min(score, 0.50)
                    if "CRITICAL_MISSING_OPTIONS" not in reasons:
                        reasons.append("CRITICAL_MISSING_OPTIONS")
                elif len(q.options) < 3:
                    score = min(score, 0.65)
                    if "FEW_OPTIONS" not in reasons:
                        reasons.append("FEW_OPTIONS")

            # Rule 3: Cross-Page Questions
            if len(q.source_pages) > 1:
                if "CROSS_PAGE_QUESTION" not in reasons:
                    reasons.append("CROSS_PAGE_QUESTION")

            # Rule 4: Answer Key Status
            if q.answer:
                if q.answer.status == AnswerStatus.UNCERTAIN:
                    if "UNCERTAIN_ANSWER" not in reasons:
                        reasons.append("UNCERTAIN_ANSWER")
                    score = min(score, 0.68)
                elif q.answer.status == AnswerStatus.NOT_FOUND:
                    if "UNMATCHED_ANSWER" not in reasons:
                        reasons.append("UNMATCHED_ANSWER")

            # Rule 5: Diagrams / Images / Tables
            if q.has_images:
                if "CONTAINS_DIAGRAM" not in reasons:
                    reasons.append("CONTAINS_DIAGRAM")
            if q.has_tables:
                if "CONTAINS_TABLE" not in reasons:
                    reasons.append("CONTAINS_TABLE")

            # Determine final categorical status
            score = round(max(0.05, min(1.0, score)), 2)
            q.confidence = score
            q.review_reasons = reasons

            if score >= settings.CONFIDENCE_THRESHOLD_HIGH and not any(
                r in ("CRITICAL_MISSING_OPTIONS", "UNCERTAIN_ANSWER", "SHORT_QUESTION_STEM")
                for r in reasons
            ):
                q.status = ExtractionStatus.CONFIDENT
                confident_count += 1
            elif score >= settings.CONFIDENCE_THRESHOLD_REVIEW:
                q.status = ExtractionStatus.PARTIALLY_EXTRACTED
                partially_extracted_count += 1
            else:
                q.status = ExtractionStatus.NEEDS_REVIEW
                needs_review_count += 1

        summary = {
            "total_questions": len(questions),
            "confident_count": confident_count,
            "partially_extracted_count": partially_extracted_count,
            "needs_review_count": needs_review_count,
            "overall_document_status": (
                ExtractionStatus.NEEDS_REVIEW if needs_review_count > 0 else ExtractionStatus.CONFIDENT
            )
        }

        return questions, summary


extraction_validator = ExtractionValidator()

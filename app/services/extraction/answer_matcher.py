import logging
import re
from typing import Dict, List, Optional, Tuple
from app.schemas.common import AnswerStatus, ExtractionStatus
from app.services.extraction.base import ExtractedAnswerKey, ExtractedQuestion

logger = logging.getLogger(__name__)


class AnswerMatcher:
    """
    Associates answer keys with extracted questions across inline sections
    or separate answer key documents.
    """

    @staticmethod
    def normalize_q_num(q_num: Optional[str]) -> str:
        """Normalize question numbers: 'Q.1', 'Question 1', '1)' -> '1'."""
        if not q_num:
            return ""
        cleaned = re.sub(r'^(?:question|q)[\.\s]*', '', q_num.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r'[\.\:\)\(\]]', '', cleaned).strip()
        return cleaned.lower()

    @staticmethod
    def parse_answer_and_explanation(val: str) -> Tuple[str, Optional[str]]:
        """Extract standardized answer key and optional explanation from text."""
        if not val:
            return "", None

        val_str = val.strip()
        expl = None

        # Look for explanation in parentheses ONLY if there is an answer before it: e.g. "B (Explanation: 2x = 10 => x = 5)"
        paren_match = re.search(r"\((?:explanation|reason|solution)?\s*:?\s*(.*?)\)$", val_str, re.IGNORECASE)
        if paren_match and paren_match.start() > 0:
            expl = paren_match.group(1).strip()
            val_str = val_str[:paren_match.start()].strip()
        elif " - " in val_str:
            parts = val_str.split(" - ", 1)
            val_str = parts[0].strip()
            expl = parts[1].strip()

        cleaned = re.sub(r'^(?:option|ans(?:wer)?)[\.\s\:]*', '', val_str, flags=re.IGNORECASE)
        cleaned = re.sub(r'[\.\:\)\(\]]', '', cleaned).strip()
        return cleaned.upper(), expl

    def associate_answers(
        self,
        questions: List[ExtractedQuestion],
        answer_keys: List[ExtractedAnswerKey],
        source_document_id: Optional[str] = None,
        association_method: str = "INLINE_KEY_SECTION"
    ) -> Tuple[List[ExtractedQuestion], List[ExtractedAnswerKey]]:
        """
        Matches answers to questions.
        Returns:
            (updated_questions, unused_answers)
        """
        answer_map: Dict[str, ExtractedAnswerKey] = {}
        unkeyed_answers: List[ExtractedAnswerKey] = []

        for ak in answer_keys:
            norm_key = self.normalize_q_num(ak.question_number)
            if norm_key:
                answer_map[norm_key] = ak
            else:
                unkeyed_answers.append(ak)

        used_answer_keys = set()

        for idx, q in enumerate(questions):
            if q.answer and q.answer.status == AnswerStatus.CONFIRMED:
                continue

            q_norm = self.normalize_q_num(q.question_number)
            matched_ak: Optional[ExtractedAnswerKey] = None
            match_status = AnswerStatus.CONFIRMED
            match_confidence = 0.95
            warnings = []

            # 1. Match by question number
            if q_norm and q_norm in answer_map:
                matched_ak = answer_map[q_norm]
                used_answer_keys.add(q_norm)
            # 2. Sequential fallback ONLY if question is unkeyed OR matching answer key is unkeyed
            elif (not q_norm) and idx < len(unkeyed_answers):
                matched_ak = unkeyed_answers[idx]
                match_status = AnswerStatus.INFERRED
                match_confidence = 0.70
                warnings.append("Answer matched by sequential position rather than explicit question number.")

            if matched_ak:
                norm_ans, expl = self.parse_answer_and_explanation(matched_ak.raw_answer)
                explanation = matched_ak.explanation or expl

                # Check option validity for MCQs
                if q.options:
                    valid_option_keys = {opt.key.upper() for opt in q.options}
                    if norm_ans not in valid_option_keys and len(norm_ans) == 1:
                        match_status = AnswerStatus.UNCERTAIN
                        match_confidence = min(match_confidence, 0.50)
                        warnings.append(
                            f"Answer key '{norm_ans}' not found among question options {list(valid_option_keys)}."
                        )
                        q.review_reasons.append("UNMATCHED_OPTION_KEY")
                        q.status = ExtractionStatus.NEEDS_REVIEW

                q.answer = ExtractedAnswerKey(
                    question_number=q.question_number,
                    raw_answer=matched_ak.raw_answer,
                    normalized_answer=norm_ans,
                    explanation=explanation,
                    source_page=matched_ak.source_page,
                    confidence=round(match_confidence * matched_ak.confidence, 2),
                    status=match_status,
                    association_method=association_method,
                    warnings=matched_ak.warnings + warnings
                )
            else:
                q.answer = ExtractedAnswerKey(
                    question_number=q.question_number,
                    raw_answer="",
                    normalized_answer="NOT_FOUND",
                    explanation=None,
                    confidence=0.0,
                    status=AnswerStatus.NOT_FOUND,
                    association_method=association_method,
                    warnings=["No corresponding answer found in answer keys."]
                )
                q.review_reasons.append("UNMATCHED_ANSWER")
                if q.confidence > 0.75:
                    q.confidence = round(q.confidence * 0.9, 2)

        unused_answers = [
            ak for ak in answer_keys
            if self.normalize_q_num(ak.question_number) not in used_answer_keys
        ]

        return questions, unused_answers


answer_matcher = AnswerMatcher()

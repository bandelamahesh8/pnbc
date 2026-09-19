import json
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from app.core.config import settings
from app.schemas.common import AnswerStatus, ExtractionStatus, QuestionType
from app.schemas.question import OptionItem
from app.services.extraction.base import (
    BaseExtractor,
    ExtractedAnswerKey,
    ExtractedQuestion,
    ExtractionResult,
)

logger = logging.getLogger(__name__)


# Pydantic schema for Gemini structured output
class GeminiOption(BaseModel):
    key: str = Field(..., description="Option label, e.g. 'A', 'B', '1', 'i'")
    text: str = Field(..., description="Option content")


class GeminiAnswer(BaseModel):
    question_number: Optional[str] = Field(None, description="Matching question number, e.g. '1', 'Q.2'")
    answer_value: str = Field(..., description="Answer text or option letter")
    explanation: Optional[str] = Field(None, description="Explanation or solution steps if available")
    source_page: Optional[int] = Field(None, description="Page where answer key was found")
    confidence: float = Field(1.0, description="Confidence of answer detection (0.0 - 1.0)")


class GeminiQuestion(BaseModel):
    question_number: Optional[str] = Field(None, description="Question number if present")
    question_text: str = Field(..., description="Full text of the question stem")
    question_type: str = Field(
        "MCQ",
        description="MCQ, MULTI_SELECT, TRUE_FALSE, FILL_IN_THE_BLANK, SHORT_ANSWER, DESCRIPTIVE"
    )
    options: List[GeminiOption] = Field(default_factory=list, description="List of options")
    source_pages: List[int] = Field(default_factory=list, description="Pages containing this question")
    confidence: float = Field(1.0, description="Extraction confidence (0.0 to 1.0)")
    has_tables: bool = Field(False, description="True if question contains a table")
    has_images: bool = Field(False, description="True if question contains a diagram or image")
    inline_answer: Optional[GeminiAnswer] = Field(None, description="Answer if provided right with question")


class GeminiExtractionResponse(BaseModel):
    document_type: str = Field("QUESTION_PAPER", description="QUESTION_PAPER, ANSWER_KEY, or COMBINED")
    page_count: int = Field(1, description="Estimated or identified total page count")
    questions: List[GeminiQuestion] = Field(default_factory=list)
    separate_answer_keys: List[GeminiAnswer] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


EXTRACTION_SYSTEM_PROMPT = """
You are an expert Document Intelligence and Examination Question Extraction AI.
Your task is to analyze the provided examination or question-bank document (PDF or image) and convert it into a structured, machine-readable JSON representation.

Strict Guidelines:
1. Identify individual questions, including:
   - Question number (e.g. "1", "Q.2", "14(a)", or null if unnumbered).
   - Full question text (including formulas, statements, and code).
   - All options (with keys 'A', 'B', 'C', 'D' or '1', '2', '3', '4' and clean text).
   - Question type: MCQ, MULTI_SELECT, TRUE_FALSE, FILL_IN_THE_BLANK, SHORT_ANSWER, DESCRIPTIVE.
   - Whether it contains embedded tables (has_tables) or diagrams/images (has_images).
   - Source page numbers (source_pages array, e.g. [1] or [1, 2] if the question spans across multiple pages).
2. Cross-Page Handling:
   - If a question stem begins on one page and its options or conclusion continue on the next page, stitch them together into a single question.
   - In source_pages, include all pages involved (e.g. [1, 2]).
3. Answer Keys:
   - If an answer key or solution section is present (at the beginning, end, or another page), extract each answer item into separate_answer_keys with the question_number, answer_value, and source_page.
   - If answers are provided inline immediately after the question, populate inline_answer.
4. Confidence Scoring & Imperfect Documents:
   - Assign a confidence score between 0.0 and 1.0:
     * High (0.85 - 1.0): Clean, crisp text, unambiguous numbering, complete options.
     * Medium (0.70 - 0.84): Minor formatting irregularities or OCR noise.
     * Low (< 0.70): Heavy blur, rotated text, missing options, cut-off questions, or uncertain numbering.
   - Record any extraction anomalies in the warnings list.
"""


class GeminiExtractor(BaseExtractor):
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL

    def is_available(self) -> bool:
        return bool(self.api_key)

    def extract(self, file_bytes: bytes, mime_type: str, filename: str) -> ExtractionResult:
        if not self.is_available():
            raise RuntimeError("Gemini API key is not configured.")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            doc_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)

            response = client.models.generate_content(
                model=self.model_name,
                contents=[
                    EXTRACTION_SYSTEM_PROMPT,
                    doc_part,
                    f"Extract all questions and answer keys from this document '{filename}'."
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiExtractionResponse,
                    temperature=0.1
                ),
            )

            parsed = GeminiExtractionResponse.model_validate_json(response.text)

            # Map to system standard ExtractedQuestion and ExtractedAnswerKey
            extracted_questions: List[ExtractedQuestion] = []
            for q in parsed.questions:
                q_type_str = q.question_type.upper()
                try:
                    q_type = QuestionType(q_type_str)
                except ValueError:
                    q_type = QuestionType.MCQ

                options_list = [OptionItem(key=opt.key, text=opt.text) for opt in q.options]

                answer_obj = None
                if q.inline_answer:
                    norm_ans = q.inline_answer.answer_value.strip().upper()
                    if norm_ans.startswith("(") and norm_ans.endswith(")"):
                        norm_ans = norm_ans[1:-1].strip()
                    answer_obj = ExtractedAnswerKey(
                        question_number=q.question_number,
                        raw_answer=q.inline_answer.answer_value,
                        normalized_answer=norm_ans,
                        explanation=q.inline_answer.explanation,
                        source_page=q.inline_answer.source_page or (q.source_pages[0] if q.source_pages else 1),
                        confidence=q.inline_answer.confidence,
                        status=AnswerStatus.CONFIRMED if q.inline_answer.confidence >= 0.8 else AnswerStatus.UNCERTAIN,
                        association_method="INLINE_QUESTION_ANSWER"
                    )

                extracted_questions.append(
                    ExtractedQuestion(
                        question_number=q.question_number,
                        question_text=q.question_text,
                        question_type=q_type,
                        options=options_list,
                        source_pages=q.source_pages or [1],
                        confidence=q.confidence,
                        has_tables=q.has_tables,
                        has_images=q.has_images,
                        answer=answer_obj,
                        metadata_info={"llm_model": self.model_name}
                    )
                )

            standalone_keys: List[ExtractedAnswerKey] = []
            for ak in parsed.separate_answer_keys:
                norm = ak.answer_value.strip().upper()
                if norm.startswith("(") and norm.endswith(")"):
                    norm = norm[1:-1].strip()
                standalone_keys.append(
                    ExtractedAnswerKey(
                        question_number=ak.question_number,
                        raw_answer=ak.answer_value,
                        normalized_answer=norm,
                        explanation=ak.explanation,
                        source_page=ak.source_page,
                        confidence=ak.confidence,
                        status=AnswerStatus.CONFIRMED if ak.confidence >= 0.8 else AnswerStatus.UNCERTAIN,
                        association_method="INLINE_KEY_SECTION"
                    )
                )

            return ExtractionResult(
                questions=extracted_questions,
                standalone_answers=standalone_keys,
                page_count=parsed.page_count,
                engine_used=f"GeminiMultimodal({self.model_name})",
                document_type=parsed.document_type,
                warnings=parsed.warnings,
                raw_metadata={"model": self.model_name}
            )

        except Exception as e:
            logger.error(f"Gemini extraction failed: {str(e)}", exc_info=True)
            raise

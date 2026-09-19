import io
import logging
import re
from typing import Dict, List, Optional, Tuple
from PIL import Image
from pypdf import PdfReader
import pdfplumber

from app.schemas.common import AnswerStatus, ExtractionStatus, QuestionType
from app.schemas.question import OptionItem
from app.services.extraction.base import (
    BaseExtractor,
    ExtractedAnswerKey,
    ExtractedQuestion,
    ExtractionResult,
)

logger = logging.getLogger(__name__)


class RuleBasedExtractor(BaseExtractor):
    """
    Deterministic rule-based and heuristic document intelligence extractor.
    Extracts structured questions, options, cross-page continuations, and answer keys
    from PDFs and images without requiring external cloud API keys.
    """

    def __init__(self):
        # Question start patterns: e.g. "1.", "Q.1", "Question 1:", "1)", "(1)", "11(a)"
        self.q_pattern = re.compile(
            r"^\s*(?:(?:Q(?:uestion)?[\.\s]*)(\d+|[ivxlcdm]+|[a-z0-9\(\)]+)|(\d+(?:\([a-z]\))?)(?:[\.\:\)]|\)\:?))\s+",
            re.IGNORECASE
        )
        # Option line prefix: e.g. "(A)", "(a)", "A.", "A)", "(1)", "(2)"
        # Note: Do not match '2.' as an option (that is question 2)
        self.opt_prefix_pattern = re.compile(
            r"^\s*(?:\(([A-Da-d1-4])\)|([A-Da-d])[\.\)])\s+",
            re.IGNORECASE
        )
        # Answer key section header pattern
        self.answer_section_pattern = re.compile(
            r"(?:^|\n)(?:==+|--+)?\s*(?:ANSWER\s*KEYS?|SOLUTIONS?|KEY\s*ANSWERS?|ANSWERS?\s*:?)\s*(?:==+|--+)?",
            re.IGNORECASE
        )
        # Answer key item pattern: e.g. "1. A", "Q1: B", "1 -> (C)", "1. Option B"
        self.answer_item_pattern = re.compile(
            r"(?:(?:Q(?:uestion)?[\.\s]*)?(\d+|[a-z]|[ivxlcdm]+)[\.\:\)\s\-\>]+(?:Option\s*)?\(?([A-Za-z0-9]+)\)?)",
            re.IGNORECASE
        )

    def extract(self, file_bytes: bytes, mime_type: str, filename: str) -> ExtractionResult:
        if mime_type == "application/pdf":
            return self._extract_pdf(file_bytes, filename)
        elif mime_type.startswith("image/"):
            return self._extract_image(file_bytes, filename)
        else:
            raise ValueError(f"Unsupported MIME type for rule extractor: {mime_type}")

    def _extract_pdf(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        pages_text: List[str] = []
        has_tables_map: Dict[int, bool] = {}
        total_pages = 1

        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                total_pages = len(pdf.pages)
                for page_idx, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    pages_text.append(text)
                    tables = page.extract_tables()
                    has_tables_map[page_idx + 1] = bool(tables)
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed, falling back to pypdf: {e}")
            reader = PdfReader(io.BytesIO(file_bytes))
            total_pages = len(reader.pages)
            for page in reader.pages:
                pages_text.append(page.extract_text() or "")

        return self._process_pages(pages_text, total_pages, has_tables_map, filename)

    def _extract_image(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            width, height = image.size
        except Exception:
            width, height = 800, 600

        text = ""
        try:
            import pytesseract
            text = pytesseract.image_to_string(image)
        except Exception:
            logger.info("pytesseract not available; using image metadata heuristic.")
            text = ""

        is_low_res = width < 500 or height < 500
        quality_confidence = 0.55 if is_low_res else 0.85

        result = self._process_pages([text], 1, {1: False}, filename)
        if is_low_res:
            result.warnings.append("Low-resolution or degraded image detected.")
            for q in result.questions:
                q.confidence = min(q.confidence, quality_confidence)
                q.review_reasons.append("LOW_RESOLUTION_IMAGE")
                q.status = ExtractionStatus.NEEDS_REVIEW
        return result

    def _process_pages(
        self,
        pages_text: List[str],
        total_pages: int,
        has_tables_map: Dict[int, bool],
        filename: str
    ) -> ExtractionResult:
        extracted_questions: List[ExtractedQuestion] = []
        standalone_answers: List[ExtractedAnswerKey] = []
        warnings: List[str] = []

        # Step 1: Detect and separate any Answer Key section
        all_pages_clean: List[Tuple[int, str]] = []
        for page_idx, page_text in enumerate(pages_text):
            page_num = page_idx + 1
            match = self.answer_section_pattern.search(page_text)
            if match:
                q_part = page_text[:match.start()].strip()
                ans_part = page_text[match.end():].strip()
                if q_part:
                    all_pages_clean.append((page_num, q_part))
                ans_items = self._parse_answer_section(ans_part, page_num)
                standalone_answers.extend(ans_items)
            else:
                all_pages_clean.append((page_num, page_text))

        # Step 2: Extract questions with cross-page stitching
        current_q: Optional[Dict] = None

        for page_num, text in all_pages_clean:
            lines = text.split("\n")
            for line in lines:
                line_str = line.strip()
                if not line_str:
                    continue

                # 1. Check if line starts with an option prefix: e.g. "(A)", "(B)", "A.", "B."
                opt_prefix_match = self.opt_prefix_pattern.match(line_str)
                if opt_prefix_match and current_q:
                    opt_key = (opt_prefix_match.group(1) or opt_prefix_match.group(2) or "").upper()
                    opt_text = line_str[opt_prefix_match.end():].strip()
                    current_q["raw_options"].append({"key": opt_key, "text": opt_text})
                    if page_num not in current_q["pages"]:
                        current_q["pages"].append(page_num)
                    continue

                # 2. Check if line starts a new question: e.g. "1.", "Q.2", "Question 3:"
                q_match = self.q_pattern.match(line_str)
                if q_match:
                    if current_q:
                        extracted_questions.append(self._build_question(current_q, has_tables_map))

                    q_num = q_match.group(1) or q_match.group(2)
                    q_text = line_str[q_match.end():].strip()
                    current_q = {
                        "question_number": q_num,
                        "text_parts": [q_text] if q_text else [],
                        "pages": [page_num],
                        "raw_options": [],
                    }
                    continue

                # 3. Continuation text
                if current_q:
                    current_q["text_parts"].append(line_str)
                    if page_num not in current_q["pages"]:
                        current_q["pages"].append(page_num)

        if current_q:
            extracted_questions.append(self._build_question(current_q, has_tables_map))

        # Step 3: Determine document type
        doc_type = "QUESTION_PAPER"
        if not extracted_questions and standalone_answers:
            doc_type = "ANSWER_KEY"
        elif extracted_questions and standalone_answers:
            doc_type = "COMBINED"

        return ExtractionResult(
            questions=extracted_questions,
            standalone_answers=standalone_answers,
            page_count=total_pages,
            engine_used="RuleBasedDocumentExtractor",
            document_type=doc_type,
            warnings=warnings,
            raw_metadata={"pages_analyzed": total_pages}
        )

    def _parse_answer_section(self, text: str, source_page: int) -> List[ExtractedAnswerKey]:
        answers: List[ExtractedAnswerKey] = []
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            for match in self.answer_item_pattern.finditer(line):
                q_num = match.group(1)
                raw_ans = match.group(2)
                norm_ans = raw_ans.strip().upper()
                answers.append(
                    ExtractedAnswerKey(
                        question_number=q_num,
                        raw_answer=raw_ans,
                        normalized_answer=norm_ans,
                        source_page=source_page,
                        confidence=0.95,
                        status=AnswerStatus.CONFIRMED,
                        association_method="INLINE_KEY_SECTION"
                    )
                )
        return answers

    def _build_question(self, q_data: Dict, has_tables_map: Dict[int, bool]) -> ExtractedQuestion:
        q_num = q_data["question_number"]
        pages = q_data["pages"]
        raw_text = " ".join(q_data["text_parts"]).strip()

        options_list: List[OptionItem] = []
        for opt in q_data["raw_options"]:
            options_list.append(OptionItem(key=opt["key"], text=opt["text"]))

        q_type = QuestionType.MCQ
        lower_text = raw_text.lower()
        if "true or false" in lower_text or "true/false" in lower_text:
            q_type = QuestionType.TRUE_FALSE
        elif "fill in the blank" in lower_text or "____" in raw_text:
            q_type = QuestionType.FILL_IN_THE_BLANK
        elif not options_list:
            if len(raw_text.split()) > 40 or "describe" in lower_text or "explain" in lower_text:
                q_type = QuestionType.DESCRIPTIVE
            else:
                q_type = QuestionType.SHORT_ANSWER
        elif len(options_list) > 4 or "select all" in lower_text:
            q_type = QuestionType.MULTI_SELECT

        has_table = any(has_tables_map.get(p, False) for p in pages)

        confidence = 0.95
        review_reasons = []

        if len(raw_text) < 15:
            confidence -= 0.25
            review_reasons.append("SHORT_QUESTION_STEM")

        if q_type == QuestionType.MCQ and len(options_list) < 3:
            confidence -= 0.30
            review_reasons.append("CRITICAL_MISSING_OPTIONS" if len(options_list) < 2 else "MISSING_OPTIONS")

        if len(pages) > 1:
            confidence -= 0.05
            review_reasons.append("CROSS_PAGE_QUESTION")

        status = ExtractionStatus.CONFIDENT
        if confidence < 0.70 or "CRITICAL_MISSING_OPTIONS" in review_reasons or "SHORT_QUESTION_STEM" in review_reasons:
            status = ExtractionStatus.NEEDS_REVIEW
        elif confidence < 0.85:
            status = ExtractionStatus.PARTIALLY_EXTRACTED

        return ExtractedQuestion(
            question_number=q_num,
            question_text=raw_text,
            question_type=q_type,
            options=options_list,
            source_pages=pages,
            confidence=max(0.1, round(confidence, 2)),
            status=status,
            review_reasons=review_reasons,
            has_tables=has_table,
            has_images=False,
            metadata_info={"pages_count": len(pages)}
        )


rule_extractor = RuleBasedExtractor()

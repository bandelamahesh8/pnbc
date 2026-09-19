from pathlib import Path
import pytest
from app.schemas.common import AnswerStatus, ExtractionStatus, QuestionType
from app.services.extraction.rule_extractor import rule_extractor
from app.services.extraction.validator import extraction_validator

SAMPLES_DIR = Path("samples/input")


def test_rule_extractor_sample_1():
    pdf_path = SAMPLES_DIR / "sample_1_standard_exam.pdf"
    assert pdf_path.exists()
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    result = rule_extractor.extract(file_bytes, "application/pdf", "sample_1_standard_exam.pdf")
    assert len(result.questions) == 3
    assert len(result.standalone_answers) == 3

    # Check Question 1
    q1 = result.questions[0]
    assert q1.question_number == "1"
    assert "Last-In, First-Out" in q1.question_text
    assert len(q1.options) == 4
    option_keys = [opt.key for opt in q1.options]
    assert option_keys == ["A", "B", "C", "D"]

    # Check Standalone Answers
    ans_map = {a.question_number: a.normalized_answer for a in result.standalone_answers}
    assert ans_map["1"] == "B"
    assert ans_map["2"] == "C"
    assert ans_map["3"] == "C"


def test_cross_page_extraction_sample_5():
    pdf_path = SAMPLES_DIR / "sample_5_cross_page.pdf"
    assert pdf_path.exists()
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    result = rule_extractor.extract(file_bytes, "application/pdf", "sample_5_cross_page.pdf")
    assert len(result.questions) >= 2

    # Question 1 spans across page 1 and page 2
    q1 = result.questions[0]
    assert 1 in q1.source_pages
    assert 2 in q1.source_pages
    assert len(q1.options) == 4
    assert q1.options[0].key == "A"
    assert q1.options[2].key == "C"


def test_uncertain_document_sample_9():
    pdf_path = SAMPLES_DIR / "sample_9_uncertain_low_confidence.pdf"
    assert pdf_path.exists()
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    result = rule_extractor.extract(file_bytes, "application/pdf", "sample_9_uncertain_low_confidence.pdf")
    questions, summary = extraction_validator.validate_and_score(result.questions, result.warnings)

    assert summary["needs_review_count"] > 0
    # Check that at least one question has low confidence
    low_conf_q = [q for q in questions if q.confidence < 0.70 or q.status == ExtractionStatus.NEEDS_REVIEW]
    assert len(low_conf_q) > 0
    reasons = low_conf_q[0].review_reasons
    assert any(r in ("CRITICAL_MISSING_OPTIONS", "SHORT_QUESTION_STEM") for r in reasons)

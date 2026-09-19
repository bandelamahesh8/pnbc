import pytest
from app.schemas.common import AnswerStatus, ExtractionStatus, QuestionType
from app.schemas.question import OptionItem
from app.services.extraction.answer_matcher import answer_matcher
from app.services.extraction.base import ExtractedAnswerKey, ExtractedQuestion


def test_answer_matcher_direct_match():
    questions = [
        ExtractedQuestion(
            question_number="1",
            question_text="What is the capital of France?",
            question_type=QuestionType.MCQ,
            options=[OptionItem(key="A", text="London"), OptionItem(key="B", text="Paris")],
            source_pages=[1],
        ),
        ExtractedQuestion(
            question_number="2",
            question_text="What is 2 + 2?",
            question_type=QuestionType.MCQ,
            options=[OptionItem(key="A", text="3"), OptionItem(key="B", text="4")],
            source_pages=[1],
        ),
    ]

    answer_keys = [
        ExtractedAnswerKey(question_number="1", raw_answer="(B)", normalized_answer="B", source_page=2),
        ExtractedAnswerKey(question_number="2", raw_answer="Option B", normalized_answer="B", source_page=2),
    ]

    matched_q, unused = answer_matcher.associate_answers(questions, answer_keys)
    assert len(unused) == 0
    assert matched_q[0].answer is not None
    assert matched_q[0].answer.normalized_answer == "B"
    assert matched_q[0].answer.status == AnswerStatus.CONFIRMED

    assert matched_q[1].answer is not None
    assert matched_q[1].answer.normalized_answer == "B"
    assert matched_q[1].answer.status == AnswerStatus.CONFIRMED


def test_answer_matcher_invalid_option_key():
    # Answer key mentions 'D', but question only has 'A' and 'B'
    questions = [
        ExtractedQuestion(
            question_number="1",
            question_text="Sample question",
            question_type=QuestionType.MCQ,
            options=[OptionItem(key="A", text="Option A"), OptionItem(key="B", text="Option B")],
            source_pages=[1],
        )
    ]

    answer_keys = [
        ExtractedAnswerKey(question_number="1", raw_answer="D", normalized_answer="D", source_page=1)
    ]

    matched_q, _ = answer_matcher.associate_answers(questions, answer_keys)
    assert matched_q[0].answer.status == AnswerStatus.UNCERTAIN
    assert "UNMATCHED_OPTION_KEY" in matched_q[0].review_reasons


def test_answer_matcher_not_found():
    questions = [
        ExtractedQuestion(
            question_number="10",
            question_text="Unanswered question",
            source_pages=[1],
        )
    ]
    # No answer for question 10
    answer_keys = [
        ExtractedAnswerKey(question_number="1", raw_answer="A", normalized_answer="A")
    ]

    matched_q, unused = answer_matcher.associate_answers(questions, answer_keys)
    assert len(unused) == 1
    assert matched_q[0].answer.status == AnswerStatus.NOT_FOUND
    assert "UNMATCHED_ANSWER" in matched_q[0].review_reasons

from __future__ import annotations

from scenario_engine.evaluation import HiddenTestResult
from scenario_engine.review import generate_review_comments


def test_review_flags_failing_hidden_test(scenario):
    result = HiddenTestResult(passed=False, stdout="", stderr="", exit_code=1)
    comments = generate_review_comments(scenario, result, "fixed it")
    assert any(not c["resolved"] for c in comments)


def test_review_approves_passing_hidden_test_with_full_explanation(scenario):
    result = HiddenTestResult(passed=True, stdout="", stderr="", exit_code=0)
    description = (
        "What was broken: uppercase extensions were rejected because the check "
        "was case-sensitive. Why: a refactor dropped .lower(). What changed: "
        "restored case-insensitive comparison and stopped swallowing the error. "
        "How verified: ran the test suite."
    )
    comments = generate_review_comments(scenario, result, description)
    assert all(c["resolved"] for c in comments)


def test_review_flags_missing_explanation(scenario):
    result = HiddenTestResult(passed=True, stdout="", stderr="", exit_code=0)
    comments = generate_review_comments(scenario, result, "fixed it")
    assert any("cover" in c["body"] for c in comments)

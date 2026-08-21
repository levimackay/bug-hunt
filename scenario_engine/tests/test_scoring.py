from __future__ import annotations

from scenario_engine.scoring import compute_score, score_code_quality, score_investigation, touched_paths

SAMPLE_DIFF = """diff --git a/app/validation.py b/app/validation.py
index 1111111..2222222 100644
--- a/app/validation.py
+++ b/app/validation.py
@@ -1,3 +1,3 @@
-def is_allowed_extension(filename):
+def is_allowed_extension(filename: str) -> bool:
     pass
diff --git a/app/main.py b/app/main.py
index 3333333..4444444 100644
--- a/app/main.py
+++ b/app/main.py
@@ -1,3 +1,3 @@
-pass
+pass
"""

SAMPLE_DIFF_WITH_OWN_TEST = SAMPLE_DIFF + """diff --git a/tests/test_upload.py b/tests/test_upload.py
index 5555555..6666666 100644
--- a/tests/test_upload.py
+++ b/tests/test_upload.py
@@ -1,2 +1,4 @@
 def test_existing():
     pass
+def test_uppercase_extension():
+    pass
"""

EXPECTED_FIX_PATHS = ["app/validation.py", "app/main.py"]
HIDDEN_TESTS_PATH = "hidden_tests/test_upload_regression.py"
CODE_QUALITY_CHECKS = ["must_not_swallow_exception", "must_add_regression_test"]


def test_touched_paths_parses_diff_git_headers():
    assert touched_paths(SAMPLE_DIFF) == {"app/validation.py", "app/main.py"}


def test_touched_paths_empty_for_blank_diff():
    assert touched_paths("") == set()


def test_compute_score_full_marks_when_everything_lines_up():
    events = [
        {"type": "git_viewed", "payload": {"action": "log"}},
        {"type": "command_run", "payload": {"action": "submit", "hidden_tests_passed": True}},
    ]
    review_comments = [{"resolved": True}]

    score = compute_score(
        hidden_test_passed=True,
        diff=SAMPLE_DIFF_WITH_OWN_TEST,
        expected_fix_paths=EXPECTED_FIX_PATHS,
        hidden_tests_path=HIDDEN_TESTS_PATH,
        events=events,
        review_comments=review_comments,
        code_quality_checks=CODE_QUALITY_CHECKS,
    )

    assert score.fix == 100
    assert score.root_cause == 100
    assert score.testing == 100
    assert score.investigation == 100
    assert score.code_quality == 100
    assert score.overall == 100


def test_compute_score_fix_is_zero_when_hidden_test_fails():
    score = compute_score(
        hidden_test_passed=False,
        diff=SAMPLE_DIFF,
        expected_fix_paths=EXPECTED_FIX_PATHS,
        hidden_tests_path=HIDDEN_TESTS_PATH,
        events=[],
        review_comments=[],
        code_quality_checks=CODE_QUALITY_CHECKS,
    )
    assert score.fix == 0


def test_root_cause_floors_at_50_when_overlap_is_zero():
    events = [{"type": "command_run", "payload": {"action": "submit"}}]
    score = compute_score(
        hidden_test_passed=True,
        diff="diff --git a/unrelated/file.py b/unrelated/file.py\n",
        expected_fix_paths=EXPECTED_FIX_PATHS,
        hidden_tests_path=HIDDEN_TESTS_PATH,
        events=events,
        review_comments=[],
        code_quality_checks=CODE_QUALITY_CHECKS,
    )
    assert score.root_cause == 50


def test_root_cause_partial_overlap():
    diff = "diff --git a/app/validation.py b/app/validation.py\n"
    score = compute_score(
        hidden_test_passed=True,
        diff=diff,
        expected_fix_paths=EXPECTED_FIX_PATHS,
        hidden_tests_path=HIDDEN_TESTS_PATH,
        events=[],
        review_comments=[],
        code_quality_checks=CODE_QUALITY_CHECKS,
    )
    assert score.root_cause == 50  # 1 of 2 expected paths touched


def test_testing_score_without_own_test_file_is_base_50():
    score = compute_score(
        hidden_test_passed=True,
        diff=SAMPLE_DIFF,
        expected_fix_paths=EXPECTED_FIX_PATHS,
        hidden_tests_path=HIDDEN_TESTS_PATH,
        events=[],
        review_comments=[],
        code_quality_checks=CODE_QUALITY_CHECKS,
    )
    assert score.testing == 50


def test_testing_score_with_own_test_file_is_100():
    score = compute_score(
        hidden_test_passed=True,
        diff=SAMPLE_DIFF_WITH_OWN_TEST,
        expected_fix_paths=EXPECTED_FIX_PATHS,
        hidden_tests_path=HIDDEN_TESTS_PATH,
        events=[],
        review_comments=[],
        code_quality_checks=CODE_QUALITY_CHECKS,
    )
    assert score.testing == 100


def test_investigation_score_subtracts_hint_costs():
    events = [
        {"type": "hint_used", "payload": {"index": 0, "cost_xp": 5}},
        {"type": "hint_used", "payload": {"index": 1, "cost_xp": 10}},
        {"type": "git_viewed", "payload": {"action": "log"}},
        {"type": "command_run", "payload": {"action": "submit"}},
    ]
    assert score_investigation(events) == 100 - 5 - 10


def test_investigation_score_penalizes_missing_git_view_before_submit():
    events = [{"type": "command_run", "payload": {"action": "submit"}}]
    assert score_investigation(events) == 85


def test_investigation_score_floors_at_zero():
    events = [{"type": "hint_used", "payload": {"cost_xp": 200}}]
    assert score_investigation(events) == 0


def test_investigation_score_no_submit_event_is_not_penalized():
    events = [{"type": "hint_used", "payload": {"cost_xp": 5}}]
    assert score_investigation(events) == 95


def test_code_quality_full_when_all_comments_resolved():
    comments = [{"resolved": True}, {"resolved": True}]
    assert score_code_quality(comments, CODE_QUALITY_CHECKS) == 100


def test_code_quality_partial_when_some_comments_unresolved():
    comments = [{"resolved": True}, {"resolved": False}]
    assert score_code_quality(comments, CODE_QUALITY_CHECKS) == 50


def test_code_quality_defaults_to_100_with_no_comments():
    assert score_code_quality([], CODE_QUALITY_CHECKS) == 100


def test_overall_is_weighted_average_rounded():
    events = [{"type": "command_run", "payload": {"action": "submit"}}]  # no git_viewed -> -15
    score = compute_score(
        hidden_test_passed=True,
        diff=SAMPLE_DIFF,  # both expected paths touched, no own test file
        expected_fix_paths=EXPECTED_FIX_PATHS,
        hidden_tests_path=HIDDEN_TESTS_PATH,
        events=events,
        review_comments=[{"resolved": True}],
        code_quality_checks=CODE_QUALITY_CHECKS,
    )
    # root_cause=100, fix=100, testing=50, investigation=85, code_quality=100
    expected = round(100 * 0.25 + 100 * 0.30 + 50 * 0.20 + 85 * 0.15 + 100 * 0.10)
    assert score.overall == expected

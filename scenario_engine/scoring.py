from __future__ import annotations

import re
from dataclasses import dataclass

_DIFF_PATH_RE = re.compile(r"^diff --git a/(.+?) b/(.+)$", re.MULTILINE)

WEIGHTS = {
    "root_cause": 0.25,
    "fix": 0.30,
    "testing": 0.20,
    "investigation": 0.15,
    "code_quality": 0.10,
}


@dataclass(frozen=True)
class Score:
    root_cause: int
    fix: int
    testing: int
    investigation: int
    code_quality: int
    overall: int

    def as_dict(self) -> dict:
        return {
            "root_cause": self.root_cause,
            "fix": self.fix,
            "testing": self.testing,
            "investigation": self.investigation,
            "code_quality": self.code_quality,
            "overall": self.overall,
        }


def touched_paths(diff: str) -> set[str]:
    """File paths (post-change side) appearing in a unified `git diff` string."""
    return {match.group(2) for match in _DIFF_PATH_RE.finditer(diff)}


def score_fix(hidden_test_passed: bool) -> int:
    return 100 if hidden_test_passed else 0


def score_root_cause(diff: str, expected_fix_paths: list[str]) -> int:
    if not expected_fix_paths:
        return 100
    overlap = len(touched_paths(diff) & set(expected_fix_paths))
    if overlap == 0:
        return 50
    return round(100 * overlap / len(expected_fix_paths))


def _is_own_test_path(path: str, hidden_tests_path: str) -> bool:
    if path == hidden_tests_path:
        return False
    parts = path.replace("\\", "/").split("/")
    basename = parts[-1]
    if basename.startswith("test_") or basename.endswith("_test.py"):
        return True
    return any(part in ("test", "tests") for part in parts[:-1])


def score_testing(diff: str, hidden_tests_path: str) -> int:
    score = 50
    if any(_is_own_test_path(p, hidden_tests_path) for p in touched_paths(diff)):
        score += 50
    return score


def _viewed_git_before_submit(events: list[dict]) -> bool:
    git_viewed_seen = False
    for event in events:
        event_type = event.get("type")
        if event_type == "git_viewed":
            git_viewed_seen = True
        elif event_type == "command_run" and event.get("payload", {}).get("action") == "submit":
            return git_viewed_seen
    return True  # no submit event in the log yet -- nothing to penalize


def score_investigation(events: list[dict]) -> int:
    score = 100
    for event in events:
        if event.get("type") == "hint_used":
            score -= event.get("payload", {}).get("cost_xp", 0)
    score = max(score, 0)
    if not _viewed_git_before_submit(events):
        score = max(score - 15, 0)
    return score


def score_code_quality(review_comments: list[dict], code_quality_checks: list[str]) -> int:
    if not code_quality_checks or not review_comments:
        return 100
    # generate_review_comments doesn't tag comments with the specific
    # review_criteria check they came from, so the fraction of code_quality_checks
    # considered satisfied is read off the fraction of review comments resolved.
    resolved = sum(1 for c in review_comments if c.get("resolved"))
    return round(100 * resolved / len(review_comments))


def compute_overall(root_cause: int, fix: int, testing: int, investigation: int, code_quality: int) -> int:
    weighted = (
        root_cause * WEIGHTS["root_cause"]
        + fix * WEIGHTS["fix"]
        + testing * WEIGHTS["testing"]
        + investigation * WEIGHTS["investigation"]
        + code_quality * WEIGHTS["code_quality"]
    )
    return round(weighted)


def compute_score(
    *,
    hidden_test_passed: bool,
    diff: str,
    expected_fix_paths: list[str],
    hidden_tests_path: str,
    events: list[dict],
    review_comments: list[dict],
    code_quality_checks: list[str],
) -> Score:
    """Pure scoring function. `events` must be in chronological order."""
    fix = score_fix(hidden_test_passed)
    root_cause = score_root_cause(diff, expected_fix_paths)
    testing = score_testing(diff, hidden_tests_path)
    investigation = score_investigation(events)
    code_quality = score_code_quality(review_comments, code_quality_checks)
    overall = compute_overall(root_cause, fix, testing, investigation, code_quality)
    return Score(
        root_cause=root_cause,
        fix=fix,
        testing=testing,
        investigation=investigation,
        code_quality=code_quality,
        overall=overall,
    )

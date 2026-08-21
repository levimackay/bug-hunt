from __future__ import annotations

from typing import TYPE_CHECKING

from scenario_engine.evaluation import HiddenTestResult

if TYPE_CHECKING:
    from scenario_engine.schema import Scenario

REVIEWER = "Marcus Rivera (Staff Eng)"

_EXPLANATION_KEYWORDS = {
    "what_was_broken": ["broken", "bug", "issue", "problem"],
    "why": ["because", "why", "root cause", "caused"],
    "what_changed": ["changed", "fix", "fixed", "restored", "updated"],
    "how_verified": ["test", "verified", "verify", "confirmed", "ran"],
}


def generate_review_comments(
    scenario: "Scenario",
    hidden_test_result: HiddenTestResult,
    pr_description: str,
) -> list[dict]:
    comments: list[dict] = []

    if hidden_test_result.passed:
        comments.append(
            {
                "author": REVIEWER,
                "body": "The regression test for this case passes now. Nice work tracking this down.",
                "resolved": True,
            }
        )
    else:
        comments.append(
            {
                "author": REVIEWER,
                "body": (
                    "The hidden regression test still fails. Take another look at the "
                    "root cause and how the fix handles it."
                ),
                "resolved": False,
            }
        )

    required = scenario.review_criteria.explanation_required
    if required:
        missing = [field for field in required if not _mentions(pr_description, field)]
        if missing:
            comments.append(
                {
                    "author": REVIEWER,
                    "body": (
                        "Your PR description doesn't clearly cover: "
                        f"{', '.join(missing)}. Please explain what was broken, why, "
                        "what changed, and how you verified it."
                    ),
                    "resolved": False,
                }
            )

    return comments


def _mentions(text: str, field: str) -> bool:
    keywords = _EXPLANATION_KEYWORDS.get(field, [field])
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)

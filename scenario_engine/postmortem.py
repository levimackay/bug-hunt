from __future__ import annotations

from typing import TYPE_CHECKING

from scenario_engine.evaluation import HiddenTestResult

if TYPE_CHECKING:
    from scenario_engine.schema import Scenario


def build_postmortem(
    scenario: "Scenario",
    events: list[dict],
    hidden_test_result: HiddenTestResult | None,
) -> dict:
    event_types = [e["type"] for e in events]
    hints_used = sum(1 for t in event_types if t == "hint_used")
    commands_run = sum(1 for t in event_types if t == "command_run")

    did_well: list[str] = []
    missed: list[str] = []

    if "git_viewed" in event_types:
        did_well.append("Checked git history to trace when the regression was introduced.")
    else:
        missed.append("Did not check git log/diff before making changes.")

    if hints_used == 0:
        did_well.append("Solved it without needing hints.")

    if hidden_test_result is not None:
        if hidden_test_result.passed:
            did_well.append("Fix passes the hidden regression test.")
        else:
            missed.append("Hidden regression test still fails.")

    return {
        "root_cause": scenario.root_cause,
        "learning_objectives": scenario.learning_objectives,
        "did_well": did_well,
        "missed": missed,
        "hints_used": hints_used,
        "commands_run": commands_run,
    }

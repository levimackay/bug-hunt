from __future__ import annotations

from scenario_engine.evaluation import HiddenTestResult
from scenario_engine.postmortem import build_postmortem


def test_postmortem_notes_missed_git_check(scenario):
    events = [{"type": "command_run"}]
    result = HiddenTestResult(passed=True, stdout="", stderr="", exit_code=0)
    postmortem = build_postmortem(scenario, events, result)
    assert postmortem["root_cause"] == scenario.root_cause
    assert any("git" in m for m in postmortem["missed"])


def test_postmortem_credits_git_check_and_no_hints(scenario):
    events = [{"type": "git_viewed"}, {"type": "command_run"}]
    result = HiddenTestResult(passed=True, stdout="", stderr="", exit_code=0)
    postmortem = build_postmortem(scenario, events, result)
    assert any("git history" in w for w in postmortem["did_well"])
    assert any("without needing hints" in w for w in postmortem["did_well"])
    assert postmortem["hints_used"] == 0


def test_postmortem_counts_hints_used(scenario):
    events = [{"type": "hint_used"}, {"type": "hint_used"}]
    postmortem = build_postmortem(scenario, events, None)
    assert postmortem["hints_used"] == 2

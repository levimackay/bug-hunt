from __future__ import annotations

from scenario_engine.loader import load_all_scenarios
from scenario_engine.tests.conftest import SCENARIOS_ROOT


def test_load_scenario_matches_yaml(scenario):
    assert scenario.id == "bug-1842-profile-upload"
    assert scenario.company == "Nexus"
    assert scenario.difficulty == "intern"
    assert scenario.entry_service == "user-service"
    assert scenario.ticket.reporter == "Customer Support"
    assert len(scenario.ticket.slack_thread) == 2
    assert scenario.ticket.slack_thread[0].author == "Priya Nandakumar (Support)"


def test_hints_are_ordered_by_cost(scenario):
    costs = [h.cost_xp for h in scenario.hints]
    assert costs == sorted(costs)
    assert costs == [5, 10, 15, 20]


def test_review_criteria_parsed(scenario):
    criteria = scenario.review_criteria
    assert criteria.checks["must_fix_case_sensitivity"] is True
    assert criteria.checks["must_add_regression_test"] is True
    assert criteria.checks["must_not_swallow_exception"] is True
    assert criteria.explanation_required == [
        "what_was_broken",
        "why",
        "what_changed",
        "how_verified",
    ]


def test_repo_dir_and_hidden_tests_path_resolve(scenario):
    assert scenario.repo_dir.is_dir()
    assert (scenario.repo_dir / ".git").is_dir()
    assert scenario.hidden_tests_path.is_file()


def test_load_all_scenarios_discovers_all_scenarios():
    scenarios = load_all_scenarios(SCENARIOS_ROOT)
    assert "bug-1842-profile-upload" in scenarios
    assert "bug-1794-search-incorrect" in scenarios
    assert "bug-1831-duplicate-notifications" in scenarios

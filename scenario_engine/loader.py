from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from scenario_engine.schema import Hint, ReviewCriteria, Scenario, Scoring, SlackMessage, Ticket


def _ensure_repo_materialized(scenario_dir: Path, repo_path: str) -> None:
    """Materialize repo/ from repo.bundle if it isn't already a real git repo.

    A scenario's repo/ needs its own real .git history on disk (the sandbox
    workspace is a filesystem copy of it, and git log/diff run against that
    copy). But a .git directory nested inside this project's own git repo
    would be recorded as an embedded/gitlink entry rather than tracked file
    contents, so the fixture history is shipped as a single-file bundle
    (repo.bundle, a normal trackable blob) and cloned out to repo/ on demand.
    """
    repo_dir = scenario_dir / repo_path
    bundle_path = scenario_dir / "repo.bundle"

    if (repo_dir / ".git").exists() or not bundle_path.exists():
        return

    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--quiet", str(bundle_path), str(repo_dir)],
        check=True,
    )


def load_scenario(scenario_dir: Path | str) -> Scenario:
    scenario_dir = Path(scenario_dir)
    yaml_path = scenario_dir / "scenario.yaml"
    data = yaml.safe_load(yaml_path.read_text())

    _ensure_repo_materialized(scenario_dir, data["repo_path"])

    ticket_data = data["ticket"]
    ticket = Ticket(
        reporter=ticket_data["reporter"],
        body=ticket_data["body"],
        slack_thread=[SlackMessage(**m) for m in ticket_data.get("slack_thread", [])],
    )

    hints = [Hint(cost_xp=h["cost_xp"], text=h["text"]) for h in data.get("hints", [])]

    review_criteria_kwargs: dict = {}
    for item in data.get("review_criteria", []):
        review_criteria_kwargs.update(item)
    review_criteria = ReviewCriteria(**review_criteria_kwargs)

    scoring_data = data.get("scoring", {})
    scoring = Scoring(
        expected_fix_paths=list(scoring_data.get("expected_fix_paths", [])),
        code_quality_checks=list(scoring_data.get("code_quality_checks", [])),
    )

    return Scenario(
        id=data["id"],
        title=data["title"],
        company=data["company"],
        severity=data["severity"],
        difficulty=data["difficulty"],
        language=data["language"],
        skills=list(data.get("skills", [])),
        learning_objectives=list(data.get("learning_objectives", [])),
        ticket=ticket,
        repo_path=data["repo_path"],
        entry_service=data["entry_service"],
        visible_test_command=data["visible_test_command"],
        root_cause=data["root_cause"],
        hidden_tests=data["hidden_tests"],
        hints=hints,
        review_criteria=review_criteria,
        scoring=scoring,
        scenario_dir=scenario_dir,
    )


def load_all_scenarios(scenarios_root: Path | str) -> dict[str, Scenario]:
    scenarios_root = Path(scenarios_root)
    if not scenarios_root.exists():
        return {}

    result: dict[str, Scenario] = {}
    for child in sorted(scenarios_root.iterdir()):
        if child.is_dir() and (child / "scenario.yaml").exists():
            scenario = load_scenario(child)
            result[scenario.id] = scenario
    return result

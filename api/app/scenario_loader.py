from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from api.app.models import Scenario as ScenarioModel
from scenario_engine.loader import load_all_scenarios


def sync_scenarios(db: Session, scenarios_root: Path) -> None:
    """Upsert every scenario.yaml under scenarios_root into the Scenario table."""
    scenarios = load_all_scenarios(scenarios_root)

    for scenario in scenarios.values():
        metadata = {
            "skills": scenario.skills,
            "learning_objectives": scenario.learning_objectives,
            "slack_thread": [
                {"author": m.author, "body": m.body} for m in scenario.ticket.slack_thread
            ],
            "root_cause": scenario.root_cause,
            "hints": [{"cost_xp": h.cost_xp, "text": h.text} for h in scenario.hints],
            "review_criteria": {
                **scenario.review_criteria.checks,
                "explanation_required": scenario.review_criteria.explanation_required,
            },
            "repo_path": scenario.repo_path,
            "hidden_tests": scenario.hidden_tests,
        }

        row = db.get(ScenarioModel, scenario.id)
        if row is None:
            row = ScenarioModel(id=scenario.id)
            db.add(row)

        row.title = scenario.title
        row.company = scenario.company
        row.severity = scenario.severity
        row.difficulty = scenario.difficulty
        row.language = scenario.language
        row.entry_service = scenario.entry_service
        row.visible_test_command = scenario.visible_test_command
        row.ticket_reporter = scenario.ticket.reporter
        row.ticket_body = scenario.ticket.body
        row.metadata_json = json.dumps(metadata)

    db.commit()

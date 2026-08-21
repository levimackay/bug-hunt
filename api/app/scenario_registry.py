from __future__ import annotations

from pathlib import Path

from scenario_engine.loader import load_all_scenarios
from scenario_engine.schema import Scenario

_registry: dict[str, Scenario] = {}


def load_registry(scenarios_root: Path) -> dict[str, Scenario]:
    global _registry
    _registry = load_all_scenarios(scenarios_root)
    return _registry


def get_scenario(scenario_id: str) -> Scenario | None:
    return _registry.get(scenario_id)


def all_scenarios() -> dict[str, Scenario]:
    return dict(_registry)

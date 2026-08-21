from __future__ import annotations

from pathlib import Path

import pytest

from scenario_engine.loader import load_scenario
from scenario_engine.schema import Scenario

SCENARIOS_ROOT = Path(__file__).resolve().parents[2] / "scenarios"
SCENARIO_DIR = SCENARIOS_ROOT / "bug-1842-profile-upload"


@pytest.fixture()
def scenario() -> Scenario:
    return load_scenario(SCENARIO_DIR)

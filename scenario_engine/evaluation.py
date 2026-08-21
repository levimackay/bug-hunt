from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sandbox.base import ExecutionBackend
    from scenario_engine.schema import Scenario


@dataclass(frozen=True)
class HiddenTestResult:
    passed: bool
    stdout: str
    stderr: str
    exit_code: int


def run_hidden_tests(
    backend: "ExecutionBackend",
    workspace_id: str,
    scenario: "Scenario",
    timeout_s: int = 30,
) -> HiddenTestResult:
    """Write the scenario's hidden test file into the workspace and run it.

    The hidden test is written transiently -- it is not part of the repo the
    user was handed. Callers must keep it out of the visible file tree (see
    scenario_engine.investigation.visible_files), never remove it from this
    evaluation step.
    """
    hidden_relpath = scenario.hidden_tests
    content = scenario.hidden_tests_path.read_text()
    backend.write_file(workspace_id, hidden_relpath, content)

    result = backend.run_command(workspace_id, ["pytest", hidden_relpath, "-q"], timeout_s=timeout_s)

    return HiddenTestResult(
        passed=result.exit_code == 0,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
    )

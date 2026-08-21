from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sandbox.base import ExecutionBackend

SCENARIOS_ROOT = Path(__file__).resolve().parents[2] / "scenarios"

_backend: "ExecutionBackend | None" = None


def get_execution_backend() -> "ExecutionBackend":
    """Production dependency: always E2B. Never overridden except in tests.

    Tests replace this via app.dependency_overrides[get_execution_backend],
    which is the only place FakeExecutionBackend is allowed to appear -- this
    function itself never imports or constructs it.
    """
    global _backend
    if _backend is None:
        from sandbox.e2b_backend import E2BExecutionBackend

        _backend = E2BExecutionBackend()
    return _backend

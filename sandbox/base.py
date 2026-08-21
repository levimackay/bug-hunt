from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

# Mirrors the allowlist enforced at the API router layer (api/app/routers/exec.py).
# Kept here too so any ExecutionBackend implementation can defend itself even if
# a caller bypasses the router.
ALLOWED_COMMANDS = frozenset({"pytest", "python", "git", "ls", "cat", "grep", "find", "diff"})


class CommandNotAllowedError(ValueError):
    pass


def validate_argv(argv: list[str]) -> None:
    if not argv:
        raise CommandNotAllowedError("empty command")
    if argv[0] not in ALLOWED_COMMANDS:
        raise CommandNotAllowedError(f"command not allowed: {argv[0]}")


@dataclass(frozen=True)
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int


class ExecutionBackend(Protocol):
    def create_workspace(self, scenario_repo_path: str) -> str:
        """Provision a fresh workspace seeded from the scenario's repo and return its id."""
        ...

    def run_command(self, workspace_id: str, argv: list[str], timeout_s: int = 20) -> ExecResult:
        """Run an argv command inside the workspace. Never a shell string."""
        ...

    def read_file(self, workspace_id: str, path: str) -> str:
        ...

    def write_file(self, workspace_id: str, path: str, content: str) -> None:
        ...

    def list_files(self, workspace_id: str) -> list[str]:
        ...

    def destroy(self, workspace_id: str) -> None:
        ...

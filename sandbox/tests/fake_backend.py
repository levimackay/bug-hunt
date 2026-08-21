from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from sandbox.base import ExecResult, validate_argv


class FakeExecutionBackend:
    """In-memory-ish ExecutionBackend for exercising the API layer without E2B.

    Each workspace is a real temp directory seeded from the scenario's actual
    repo, so pytest/git/etc. run for real -- this project treats "nothing
    simulated as fake strings" as a hard requirement, so this fake only stands
    in for the network boundary to E2B, never for command execution itself.

    Only ever wired in from test code (see api/tests/conftest.py). Must never
    be importable from production wiring -- api/app/deps.py only ever
    constructs E2BExecutionBackend.
    """

    def __init__(self) -> None:
        self._workspaces: dict[str, Path] = {}

    def create_workspace(self, scenario_repo_path: str) -> str:
        workspace_id = uuid.uuid4().hex
        workspace_dir = Path(tempfile.mkdtemp(prefix="bug-hunt-fake-"))
        shutil.copytree(scenario_repo_path, workspace_dir, dirs_exist_ok=True)
        self._workspaces[workspace_id] = workspace_dir
        return workspace_id

    def run_command(self, workspace_id: str, argv: list[str], timeout_s: int = 20) -> ExecResult:
        validate_argv(argv)
        workspace_dir = self._require(workspace_id)
        resolved = self._resolve_argv(argv)
        proc = subprocess.run(
            resolved,
            cwd=workspace_dir,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        return ExecResult(stdout=proc.stdout, stderr=proc.stderr, exit_code=proc.returncode)

    def read_file(self, workspace_id: str, path: str) -> str:
        return (self._require(workspace_id) / path).read_text()

    def write_file(self, workspace_id: str, path: str, content: str) -> None:
        full_path = self._require(workspace_id) / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    def list_files(self, workspace_id: str) -> list[str]:
        workspace_dir = self._require(workspace_id)
        files: list[str] = []
        for root, dirs, filenames in os.walk(workspace_dir):
            dirs[:] = [d for d in dirs if d != ".git"]
            for filename in filenames:
                full_path = Path(root) / filename
                files.append(full_path.relative_to(workspace_dir).as_posix())
        return sorted(files)

    def destroy(self, workspace_id: str) -> None:
        workspace_dir = self._workspaces.pop(workspace_id, None)
        if workspace_dir is not None:
            shutil.rmtree(workspace_dir, ignore_errors=True)

    def _require(self, workspace_id: str) -> Path:
        try:
            return self._workspaces[workspace_id]
        except KeyError as exc:
            raise ValueError(f"unknown workspace: {workspace_id}") from exc

    @staticmethod
    def _resolve_argv(argv: list[str]) -> list[str]:
        # Route bare "python"/"pytest" through the interpreter actually running
        # this test suite, regardless of the parent shell's PATH/activation state.
        if not argv:
            return argv
        head, rest = argv[0], argv[1:]
        if head == "python":
            return [sys.executable, *rest]
        if head == "pytest":
            return [sys.executable, "-m", "pytest", *rest]
        return argv

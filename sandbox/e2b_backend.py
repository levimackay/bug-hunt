from __future__ import annotations

import os
import shlex
import tarfile
import tempfile

from e2b import Sandbox

from sandbox.base import ExecResult, validate_argv

WORKSPACE_DIR = "/home/user/workspace"


class E2BExecutionBackend:
    """The only production ExecutionBackend. Requires E2B_API_KEY.

    E2B's Commands.run() takes a single shell-parsed command string rather than
    an argv list, since that is the shape of the underlying SDK/API. To honor
    the "never shell=True, never string-interpolated commands" rule in spirit,
    every argv list handed to this backend is combined with shlex.join(), which
    quotes each token individually -- no argument can escape its own position or
    inject additional shell syntax the way naive f-string interpolation could.
    """

    def __init__(self) -> None:
        api_key = os.environ.get("E2B_API_KEY")
        if not api_key:
            raise RuntimeError("set E2B_API_KEY to run investigations")
        self._api_key = api_key
        self._sandboxes: dict[str, Sandbox] = {}

    def create_workspace(self, scenario_repo_path: str) -> str:
        sandbox = Sandbox.create(api_key=self._api_key)
        sandbox.commands.run(f"mkdir -p {shlex.quote(WORKSPACE_DIR)}")

        archive_path = self._build_archive(scenario_repo_path)
        remote_archive = "/home/user/repo.tar.gz"
        try:
            with open(archive_path, "rb") as fh:
                sandbox.files.write(remote_archive, fh.read())
        finally:
            os.remove(archive_path)

        sandbox.commands.run(shlex.join(["tar", "xzf", remote_archive, "-C", WORKSPACE_DIR]))

        workspace_id = sandbox.sandbox_id
        self._sandboxes[workspace_id] = sandbox
        return workspace_id

    def run_command(self, workspace_id: str, argv: list[str], timeout_s: int = 20) -> ExecResult:
        validate_argv(argv)
        sandbox = self._get(workspace_id)
        result = sandbox.commands.run(shlex.join(argv), cwd=WORKSPACE_DIR, timeout=timeout_s)
        return ExecResult(stdout=result.stdout, stderr=result.stderr, exit_code=result.exit_code)

    def read_file(self, workspace_id: str, path: str) -> str:
        sandbox = self._get(workspace_id)
        return sandbox.files.read(f"{WORKSPACE_DIR}/{path}")

    def write_file(self, workspace_id: str, path: str, content: str) -> None:
        sandbox = self._get(workspace_id)
        sandbox.files.write(f"{WORKSPACE_DIR}/{path}", content)

    def list_files(self, workspace_id: str) -> list[str]:
        sandbox = self._get(workspace_id)
        result = sandbox.commands.run(
            shlex.join(["find", ".", "-type", "f", "-not", "-path", "./.git/*"]),
            cwd=WORKSPACE_DIR,
        )
        return [line[2:] for line in result.stdout.splitlines() if line.startswith("./")]

    def destroy(self, workspace_id: str) -> None:
        sandbox = self._sandboxes.pop(workspace_id, None)
        if sandbox is not None:
            sandbox.kill()

    def _get(self, workspace_id: str) -> Sandbox:
        try:
            return self._sandboxes[workspace_id]
        except KeyError as exc:
            raise ValueError(f"unknown workspace: {workspace_id}") from exc

    @staticmethod
    def _build_archive(scenario_repo_path: str) -> str:
        fd, archive_path = tempfile.mkstemp(suffix=".tar.gz")
        os.close(fd)
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(scenario_repo_path, arcname=".")
        return archive_path

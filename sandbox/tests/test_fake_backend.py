from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from sandbox.base import CommandNotAllowedError
from sandbox.tests.fake_backend import FakeExecutionBackend


@pytest.fixture()
def seeded_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "hello.txt").write_text("hello\n")
    return repo


def test_create_workspace_copies_repo(seeded_repo: Path):
    backend = FakeExecutionBackend()
    workspace_id = backend.create_workspace(str(seeded_repo))
    assert backend.read_file(workspace_id, "hello.txt") == "hello\n"
    backend.destroy(workspace_id)


def test_write_then_read_file(seeded_repo: Path):
    backend = FakeExecutionBackend()
    workspace_id = backend.create_workspace(str(seeded_repo))
    backend.write_file(workspace_id, "nested/new.txt", "content")
    assert backend.read_file(workspace_id, "nested/new.txt") == "content"
    backend.destroy(workspace_id)


def test_list_files_excludes_git_dir(seeded_repo: Path):
    (seeded_repo / ".git").mkdir()
    (seeded_repo / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    backend = FakeExecutionBackend()
    workspace_id = backend.create_workspace(str(seeded_repo))
    files = backend.list_files(workspace_id)
    assert "hello.txt" in files
    assert not any(f.startswith(".git/") for f in files)
    backend.destroy(workspace_id)


def test_run_command_rejects_disallowed_command(seeded_repo: Path):
    backend = FakeExecutionBackend()
    workspace_id = backend.create_workspace(str(seeded_repo))
    with pytest.raises(CommandNotAllowedError):
        backend.run_command(workspace_id, ["rm", "-rf", "."])


def test_run_command_executes_argv_for_real(seeded_repo: Path):
    backend = FakeExecutionBackend()
    workspace_id = backend.create_workspace(str(seeded_repo))
    result = backend.run_command(workspace_id, ["cat", "hello.txt"])
    assert result.exit_code == 0
    assert result.stdout == "hello\n"

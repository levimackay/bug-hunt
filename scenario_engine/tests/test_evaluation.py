from __future__ import annotations

from sandbox.tests.fake_backend import FakeExecutionBackend
from scenario_engine.evaluation import run_hidden_tests

FIXED_VALIDATION = '''ALLOWED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif")


def is_allowed_extension(filename: str) -> bool:
    return filename.lower().endswith(ALLOWED_EXTENSIONS)


def validate_extension(filename: str) -> None:
    if not is_allowed_extension(filename):
        raise ValueError(f"Unsupported file type: {filename}")
'''

FIXED_MAIN = '''from fastapi import FastAPI, HTTPException, UploadFile, File

from app.storage import save_profile_photo
from app.thumbnails import generate_thumbnail
from app.validation import validate_extension

app = FastAPI()


@app.post("/upload")
async def upload_profile_photo(file: UploadFile = File(...)):
    try:
        validate_extension(file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    contents = await file.read()
    save_profile_photo(file.filename, contents)
    generate_thumbnail(file.filename)
    return {"status": "upload received"}
'''


def test_hidden_tests_fail_before_fix(scenario):
    backend = FakeExecutionBackend()
    workspace_id = backend.create_workspace(str(scenario.repo_dir))

    result = run_hidden_tests(backend, workspace_id, scenario)

    assert result.passed is False
    assert result.exit_code != 0
    backend.destroy(workspace_id)


def test_hidden_tests_pass_after_fix(scenario):
    backend = FakeExecutionBackend()
    workspace_id = backend.create_workspace(str(scenario.repo_dir))

    backend.write_file(workspace_id, "app/validation.py", FIXED_VALIDATION)
    backend.write_file(workspace_id, "app/main.py", FIXED_MAIN)

    result = run_hidden_tests(backend, workspace_id, scenario)

    assert result.passed is True
    assert result.exit_code == 0
    backend.destroy(workspace_id)

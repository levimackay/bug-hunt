import os

from fastapi.testclient import TestClient

from app.main import app
from app.storage import STORAGE_DIR

client = TestClient(app)


def _cleanup(filename: str) -> None:
    path = os.path.join(STORAGE_DIR, filename)
    if os.path.exists(path):
        os.remove(path)


def test_uppercase_image_extension_is_persisted():
    _cleanup("IMG_0421.JPG")
    response = client.post(
        "/upload", files={"file": ("IMG_0421.JPG", b"fakeimagebytes", "image/jpeg")}
    )
    assert response.status_code == 200
    assert os.path.exists(os.path.join(STORAGE_DIR, "IMG_0421.JPG"))
    _cleanup("IMG_0421.JPG")


def test_uppercase_invalid_extension_is_still_rejected():
    _cleanup("MALWARE.EXE")
    response = client.post(
        "/upload", files={"file": ("MALWARE.EXE", b"binary", "application/octet-stream")}
    )
    assert response.status_code >= 400
    assert not os.path.exists(os.path.join(STORAGE_DIR, "MALWARE.EXE"))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_retried_notify_is_not_sent_twice():
    payload = {"event_id": 8842, "message": "Order #8842 confirmed"}

    first = client.post("/notify", json=payload)
    second = client.post("/notify", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "sent"
    assert second.json()["status"] == "duplicate"

    listing = client.get("/notifications")
    matching = [
        n for n in listing.json()["notifications"] if n["event_id"] == 8842
    ]
    assert len(matching) == 1

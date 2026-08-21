from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_search_finds_product_matching_at_end_of_text():
    response = client.get("/search", params={"q": "cable"})
    assert response.status_code == 200
    names = [p["name"] for p in response.json()["results"]]
    assert "Braided USB-C to USB-C" in names

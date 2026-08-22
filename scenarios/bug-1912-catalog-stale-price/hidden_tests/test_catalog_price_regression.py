from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_price_update_invalidates_the_cached_sku_product():
    warm = client.get("/products/NX-4471-BLK")
    assert warm.status_code == 200
    assert warm.json()["price"] == 24.5

    update = client.put("/products/NX-4471-BLK/price", json={"price": 19.99})
    assert update.status_code == 200
    assert update.json()["price"] == 19.99

    after = client.get("/products/NX-4471-BLK")
    assert after.status_code == 200
    assert after.json()["price"] == 19.99


def test_second_price_update_is_also_visible():
    client.get("/products/NX-7702-SLV")
    client.put("/products/NX-7702-SLV/price", json={"price": 79.0})
    assert client.get("/products/NX-7702-SLV").json()["price"] == 79.0

    client.put("/products/NX-7702-SLV/price", json={"price": 71.5})
    assert client.get("/products/NX-7702-SLV").json()["price"] == 71.5

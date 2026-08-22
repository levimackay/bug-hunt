from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

BUNDLE_LINES = [
    {"sku": "SKU-DESK-01", "unit_price_cents": 4000, "quantity": 1},
    {"sku": "SKU-CHAIR-07", "unit_price_cents": 6000, "quantity": 1},
]


def _bundle_payload(code: str) -> dict:
    return {
        "order_id": "ORD-2002",
        "order_type": "bundle",
        "lines": BUNDLE_LINES,
        "code": code,
    }


def test_expired_code_is_rejected_on_bundle_order():
    response = client.post("/apply-discount", json=_bundle_payload("BLACKFRIDAY24"))
    assert response.status_code == 400
    assert "expired" in response.json()["detail"]


def test_code_at_redemption_limit_is_rejected_on_bundle_order():
    response = client.post("/apply-discount", json=_bundle_payload("FOUNDERS50"))
    assert response.status_code == 400
    assert "redemption limit" in response.json()["detail"]


def test_unknown_code_is_rejected_on_bundle_order():
    response = client.post("/apply-discount", json=_bundle_payload("NOT-A-REAL-CODE"))
    assert response.status_code == 400
    assert "Unknown discount code" in response.json()["detail"]


def test_valid_code_still_applies_on_bundle_order():
    response = client.post("/apply-discount", json=_bundle_payload("WELCOME15"))
    assert response.status_code == 200
    body = response.json()
    assert body["subtotal_cents"] == 9500
    assert body["discount_cents"] == 1425
    assert body["total_cents"] == 8075
    assert body["code_applied"] == "WELCOME15"


def test_expired_code_is_still_rejected_on_standard_order():
    response = client.post(
        "/apply-discount",
        json={
            "order_id": "ORD-1001",
            "lines": [{"sku": "SKU-DESK-01", "unit_price_cents": 4000, "quantity": 1}],
            "code": "BLACKFRIDAY24",
        },
    )
    assert response.status_code == 400

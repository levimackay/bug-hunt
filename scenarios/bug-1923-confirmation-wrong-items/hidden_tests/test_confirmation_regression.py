from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_each_orders_email_lists_that_orders_own_items():
    first = client.post("/orders/NX-4471/confirmation-email")
    second = client.post("/orders/NX-4472/confirmation-email")

    assert first.status_code == 200
    assert second.status_code == 200

    first_body = first.json()["body"]
    assert "2 x Aeropress Filter Pack (TB-330)" in first_body
    assert "1 x Ceramic Pour-Over Cone (TB-118)" in first_body
    assert "Cold Brew Growler" not in first_body
    assert "Burr Grinder Mk II" not in first_body

    second_body = second.json()["body"]
    assert "1 x Cold Brew Growler (GR-905)" in second_body
    assert "1 x Burr Grinder Mk II (GD-221)" in second_body
    assert "Aeropress Filter Pack" not in second_body
    assert "Ceramic Pour-Over Cone" not in second_body


def test_outbox_entries_keep_each_orders_own_items():
    client.post("/orders/NX-4473/confirmation-email")
    client.post("/orders/NX-4474/confirmation-email")

    outbox = client.get("/outbox").json()["outbox"]
    by_order = {entry["order_id"]: entry for entry in outbox}

    assert "3 x Paper Filter Refill (TB-018)" in by_order["NX-4473"]["body"]
    assert "Travel Kettle" not in by_order["NX-4473"]["body"]

    assert "1 x Travel Kettle (KT-440)" in by_order["NX-4474"]["body"]
    assert "Paper Filter Refill" not in by_order["NX-4474"]["body"]

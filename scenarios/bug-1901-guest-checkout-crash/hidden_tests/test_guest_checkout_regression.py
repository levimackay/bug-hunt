from fastapi.testclient import TestClient

from app.customers import CUSTOMERS
from app.main import app
from app.models import Customer, LineItem, Order
from app.pricing import build_order_summary

client = TestClient(app, raise_server_exceptions=False)

ITEMS = [
    {
        "sku": "NX-CBL-01",
        "description": "Braided USB-C cable, 2m",
        "unit_price_cents": 1200,
        "quantity": 2,
    },
    {
        "sku": "NX-HUB-04",
        "description": "7-port powered USB hub",
        "unit_price_cents": 4500,
        "quantity": 1,
    },
]


def test_guest_checkout_summary_does_not_error():
    response = client.post(
        "/checkout/summary",
        json={"order_id": "ord_guest_1", "items": ITEMS},
    )
    assert response.status_code == 200, f"guest checkout returned {response.status_code}"
    body = response.json()
    assert body["customer_id"] == "guest"
    assert body["subtotal_cents"] == 6900
    assert body["discount_cents"] == 0
    assert body["tax_cents"] == 483
    assert body["total_cents"] == 7383


def test_order_summary_for_a_customer_without_a_membership_tier():
    order = Order(
        id="ord_guest_2",
        customer=Customer(id="guest", name="Guest"),
        items=[LineItem(**item) for item in ITEMS],
    )
    summary = build_order_summary(order)
    assert summary["discount_cents"] == 0
    assert summary["total_cents"] == 7383


def test_members_still_receive_their_loyalty_discount():
    gold = client.post(
        "/checkout/summary",
        json={"order_id": "ord_member_1", "customer_id": "cus_1042", "items": ITEMS},
    )
    assert gold.status_code == 200
    assert gold.json()["discount_cents"] == 1035
    assert gold.json()["total_cents"] == 6275

    silver = client.post(
        "/checkout/summary",
        json={"order_id": "ord_member_2", "customer_id": "cus_2277", "items": ITEMS},
    )
    assert silver.status_code == 200
    assert silver.json()["discount_cents"] == 690
    assert silver.json()["total_cents"] == 6644


def test_every_seeded_member_tier_still_discounts():
    for customer_id, customer in CUSTOMERS.items():
        response = client.post(
            "/checkout/summary",
            json={"order_id": f"ord_{customer_id}", "customer_id": customer_id, "items": ITEMS},
        )
        assert response.status_code == 200
        expected = 6900 * customer.membership_tier.discount_pct // 100
        assert response.json()["discount_cents"] == expected

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PAGE_SIZE = 10

PAGE_1_IDS = [
    "ORD-2025",
    "ORD-2024",
    "ORD-2023",
    "ORD-2022",
    "ORD-2021",
    "ORD-2020",
    "ORD-2019",
    "ORD-2018",
    "ORD-2017",
    "ORD-2016",
]

PAGE_2_IDS = [
    "ORD-2015",
    "ORD-2014",
    "ORD-2013",
    "ORD-2012",
    "ORD-2011",
    "ORD-2010",
    "ORD-2009",
    "ORD-2008",
    "ORD-2007",
    "ORD-2006",
]

PAGE_3_IDS = [
    "ORD-2005",
    "ORD-2004",
    "ORD-2003",
    "ORD-2002",
    "ORD-2001",
]


def _page_ids(page: int, page_size: int = PAGE_SIZE) -> list[str]:
    response = client.get("/orders", params={"page": page, "page_size": page_size})
    assert response.status_code == 200
    return [order["id"] for order in response.json()["orders"]]


def test_first_page_starts_at_the_newest_order():
    assert _page_ids(1) == PAGE_1_IDS


def test_second_page_continues_where_the_first_page_ended():
    assert _page_ids(2) == PAGE_2_IDS


def test_last_page_returns_the_remaining_orders():
    assert _page_ids(3) == PAGE_3_IDS


def test_paging_through_the_history_yields_every_order_exactly_once():
    seen = _page_ids(1) + _page_ids(2) + _page_ids(3)
    assert seen == PAGE_1_IDS + PAGE_2_IDS + PAGE_3_IDS
    assert len(set(seen)) == 25


def test_a_smaller_page_size_pages_from_the_same_starting_point():
    assert _page_ids(1, page_size=5) == PAGE_1_IDS[:5]
    assert _page_ids(2, page_size=5) == PAGE_1_IDS[5:]

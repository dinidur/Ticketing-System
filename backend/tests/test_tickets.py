import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.db.session import SessionLocal
from app.services import ticket_service
from app.services.ticket_service import TicketAlreadyAssignedError

API = "/api/v1/tickets"


def make_ticket(client, **overrides) -> dict:
    payload = {
        "title": "Cannot log in",
        "description": "Login fails",
        "priority": "high",
    }
    payload.update(overrides)
    response = client.post(API, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------- Health ----------


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------- Create ----------


def test_create_ticket(client):
    ticket = make_ticket(client, tags=["Login", "bug", "login"])

    assert ticket["id"] == 1
    assert ticket["priority"] == "high"
    assert ticket["tags"] == ["login", "bug"]  # lowercased + de-duplicated
    assert ticket["assigned_to"] is None
    assert ticket["assigned_at"] is None


def test_create_ticket_uses_default_priority(client):
    response = client.post(API, json={"title": "No priority", "description": "x"})
    assert response.status_code == 201
    assert response.json()["priority"] == "medium"


@pytest.mark.parametrize(
    "payload",
    [
        {"title": "", "description": "x"},  # empty title
        {"title": "ab", "description": "x"},  # title too short
        {"title": "Valid title", "description": ""},  # empty description
        {"title": "Valid title", "description": "x", "priority": "urgent"},  # bad enum
        {
            "title": "Valid title",
            "description": "x",
            "tags": ["t"] * 11,
        },  # too many tags
        {"description": "x"},  # missing title
    ],
)
def test_create_ticket_validation_errors(client, payload):
    assert client.post(API, json=payload).status_code == 422


# ---------- Read ----------


def test_get_ticket(client):
    created = make_ticket(client)
    response = client.get(f"{API}/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Cannot log in"


def test_get_missing_ticket_returns_404(client):
    assert client.get(f"{API}/999").status_code == 404


# ---------- List + pagination ----------


def test_pagination_walks_all_pages_without_duplicates(client):
    created_ids = [make_ticket(client, title=f"Ticket {i}")["id"] for i in range(25)]

    seen_ids, cursor, pages = [], None, 0
    while True:
        params = {"limit": 10} | ({"cursor": cursor} if cursor else {})
        body = client.get(API, params=params).json()
        seen_ids += [t["id"] for t in body["items"]]
        pages += 1
        cursor = body["next_cursor"]
        if not body["has_more"]:
            break

    assert pages == 3  # 10 + 10 + 5
    assert len(seen_ids) == len(set(seen_ids)) == 25  # no duplicates, nothing missed
    assert seen_ids == sorted(created_ids, reverse=True)  # newest first


def test_list_filters(client):
    make_ticket(client, priority="critical", tags=["vpn"])
    make_ticket(client, priority="low", tags=["billing"])
    claimed = make_ticket(client, priority="critical")
    client.post(f"{API}/{claimed['id']}/assign", json={"email": "a@support.io"})

    def ids(**params):
        return [t["id"] for t in client.get(API, params=params).json()["items"]]

    assert len(ids(priority="critical")) == 2
    assert len(ids(priority="critical", assigned="false")) == 1
    assert ids(assigned="true") == [claimed["id"]]
    assert len(ids(tag="vpn")) == 1


def test_invalid_cursor_returns_400(client):
    assert client.get(API, params={"cursor": "not-a-cursor"}).status_code == 400


def test_limit_above_max_returns_422(client):
    assert client.get(API, params={"limit": 500}).status_code == 422


# ---------- Assign ----------


def test_assign_ticket(client):
    ticket = make_ticket(client)
    response = client.post(f"{API}/{ticket['id']}/assign", json={"email": "Alice@Support.io"})

    assert response.status_code == 200
    body = response.json()
    assert body["assigned_to"] == "alice@support.io"  # normalised
    assert body["assigned_at"] is not None


def test_assign_already_assigned_returns_409_and_keeps_owner(client):
    ticket = make_ticket(client)
    client.post(f"{API}/{ticket['id']}/assign", json={"email": "alice@support.io"})

    response = client.post(f"{API}/{ticket['id']}/assign", json={"email": "bob@support.io"})

    assert response.status_code == 409
    assert client.get(f"{API}/{ticket['id']}").json()["assigned_to"] == "alice@support.io"


def test_assign_missing_ticket_returns_404(client):
    response = client.post(f"{API}/999/assign", json={"email": "a@support.io"})
    assert response.status_code == 404


def test_assign_invalid_email_returns_422(client):
    ticket = make_ticket(client)
    response = client.post(f"{API}/{ticket['id']}/assign", json={"email": "not-an-email"})
    assert response.status_code == 422


def test_concurrent_claims_only_one_agent_wins(client):
    """The core business rule: under concurrency, exactly one claim succeeds."""
    ticket_id = make_ticket(client, priority="critical")["id"]
    agents = 20
    barrier = threading.Barrier(agents)

    def claim(agent_no: int) -> str:
        # Each "agent" gets its own DB session, like separate HTTP requests
        with SessionLocal() as db:
            barrier.wait()  # everyone fires at the same moment
            try:
                ticket_service.assign_ticket(db, ticket_id, f"agent{agent_no}@support.io")
                return "won"
            except TicketAlreadyAssignedError:
                return "conflict"

    with ThreadPoolExecutor(max_workers=agents) as pool:
        results = list(pool.map(claim, range(agents)))

    assert results.count("won") == 1
    assert results.count("conflict") == agents - 1

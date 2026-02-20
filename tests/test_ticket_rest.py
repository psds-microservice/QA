"""REST API ticket-service: /api/v1/tickets (CRUD)."""

from __future__ import annotations

import uuid

import pytest

from qa_tests.http_client import TicketServiceClient

# ID тикета — число (uint64), не UUID
NONEXISTENT_TICKET_ID = "999999"
# Невалидный id (UUID вместо числа) — сервис должен вернуть 400
INVALID_ID_UUID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.smoke
def test_list_tickets_empty(ticket_service_client: TicketServiceClient) -> None:
    """GET /api/v1/tickets возвращает 200 с объектом {tickets: [], total: 0}."""
    resp = ticket_service_client.list_tickets()
    assert resp.status_code == 200
    assert resp.json is not None
    assert "tickets" in resp.json
    assert "total" in resp.json


@pytest.mark.smoke
def test_list_tickets_with_params(ticket_service_client: TicketServiceClient) -> None:
    """GET /api/v1/tickets?limit=10&offset=0 возвращает 200 с tickets и total."""
    resp = ticket_service_client.list_tickets(limit=10, offset=0)
    assert resp.status_code == 200
    assert resp.json is not None
    assert "tickets" in resp.json
    assert "total" in resp.json


@pytest.mark.smoke
def test_create_and_get_ticket(ticket_service_client: TicketServiceClient) -> None:
    """POST /api/v1/tickets создаёт тикет, GET возвращает его."""
    session_id = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    operator_id = str(uuid.uuid4())
    payload = {
        "subject": "Test ticket",
        "notes": "Test notes",
        "session_id": session_id,
        "client_id": client_id,
        "operator_id": operator_id,
    }
    create = ticket_service_client.create_ticket(payload)
    assert create.status_code == 201  # Created
    assert create.json is not None
    ticket_id = create.json.get("id")
    assert ticket_id is not None

    # Get by id (ID — число, конвертируем в строку)
    get_resp = ticket_service_client.get_ticket(str(ticket_id))
    assert get_resp.status_code == 200
    assert get_resp.json is not None
    assert get_resp.json.get("id") == ticket_id
    assert get_resp.json.get("subject") == "Test ticket"


@pytest.mark.smoke
def test_update_ticket(ticket_service_client: TicketServiceClient) -> None:
    """PUT /api/v1/tickets/:id обновляет тикет."""
    session_id = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    operator_id = str(uuid.uuid4())
    create_payload = {
        "subject": "Original subject",
        "notes": "Original notes",
        "session_id": session_id,
        "client_id": client_id,
        "operator_id": operator_id,
    }
    create = ticket_service_client.create_ticket(create_payload)
    assert create.status_code == 201  # Created
    assert create.json is not None
    ticket_id = create.json.get("id")
    assert ticket_id is not None

    # Update (ID — число, конвертируем в строку)
    update_payload = {
        "subject": "Updated subject",
        "notes": "Updated notes",
        "status": "closed",
    }
    update = ticket_service_client.update_ticket(str(ticket_id), update_payload)
    assert update.status_code == 200
    assert update.json is not None
    assert update.json.get("subject") == "Updated subject"
    assert update.json.get("status") == "closed"


@pytest.mark.negative
def test_get_ticket_invalid_id(ticket_service_client: TicketServiceClient) -> None:
    """GET /api/v1/tickets/:id с невалидным id (UUID) — 400 (Кейс A)."""
    resp = ticket_service_client.get_ticket(INVALID_ID_UUID)
    assert resp.status_code == 400
    if resp.json:
        assert "error" in resp.json or "invalid" in str(resp.json).lower()


@pytest.mark.negative
def test_update_ticket_invalid_id(ticket_service_client: TicketServiceClient) -> None:
    """PUT /api/v1/tickets/:id с невалидным id (UUID) — 400 (Кейс A)."""
    payload = {"subject": "Test", "notes": "Test"}
    resp = ticket_service_client.update_ticket(INVALID_ID_UUID, payload)
    assert resp.status_code == 400
    if resp.json:
        assert "error" in resp.json or "invalid" in str(resp.json).lower()


@pytest.mark.negative
def test_get_ticket_not_found(ticket_service_client: TicketServiceClient) -> None:
    """GET /api/v1/tickets/:id для несуществующего числового id — 404 (Кейс B)."""
    resp = ticket_service_client.get_ticket(NONEXISTENT_TICKET_ID)
    assert resp.status_code == 404


@pytest.mark.negative
def test_update_ticket_not_found(ticket_service_client: TicketServiceClient) -> None:
    """PUT /api/v1/tickets/:id для несуществующего числового id — 404 (Кейс B)."""
    payload = {"subject": "Test", "notes": "Test"}
    resp = ticket_service_client.update_ticket(NONEXISTENT_TICKET_ID, payload)
    assert resp.status_code == 404


@pytest.mark.negative
def test_create_ticket_invalid_body(ticket_service_client: TicketServiceClient) -> None:
    """POST /api/v1/tickets без обязательных полей — 400."""
    resp = ticket_service_client.create_ticket({})
    assert resp.status_code == 400

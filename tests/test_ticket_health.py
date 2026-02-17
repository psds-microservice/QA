"""Health/ready для ticket-service."""

from __future__ import annotations

import pytest

from qa_tests.http_client import TicketServiceClient


@pytest.mark.smoke
def test_ticket_health_ok(ticket_service_client: TicketServiceClient) -> None:
    """GET /health возвращает 200."""
    resp = ticket_service_client.health()
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("status") == "ok"


@pytest.mark.smoke
def test_ticket_ready_ok(ticket_service_client: TicketServiceClient) -> None:
    """GET /ready возвращает 200."""
    resp = ticket_service_client.ready()
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("status") == "ready"

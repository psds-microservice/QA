"""Health/ready для session-manager-service."""

from __future__ import annotations

import pytest

from qa_tests.http_client import SessionManagerServiceClient


@pytest.mark.smoke
def test_session_manager_health_ok(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """GET /health возвращает 200 и service: session-manager-service."""
    resp = session_manager_service_client.health()
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("service") == "session-manager-service"


@pytest.mark.smoke
def test_session_manager_ready_ok(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """GET /ready возвращает 200."""
    resp = session_manager_service_client.ready()
    assert resp.status_code == 200

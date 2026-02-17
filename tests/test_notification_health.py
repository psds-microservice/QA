"""Health/ready для notification-service."""

from __future__ import annotations

import pytest

from qa_tests.http_client import NotificationServiceClient


@pytest.mark.smoke
def test_notification_health_ok(
    notification_service_client: NotificationServiceClient,
) -> None:
    """GET /health возвращает 200 и service: notification-service."""
    resp = notification_service_client.health()
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("service") == "notification-service"


@pytest.mark.smoke
def test_notification_ready_ok(
    notification_service_client: NotificationServiceClient,
) -> None:
    """GET /ready возвращает 200."""
    resp = notification_service_client.ready()
    assert resp.status_code == 200

"""REST API notification-service: POST /notify/session/:id."""

from __future__ import annotations

import uuid

import pytest

from qa_tests.http_client import NotificationServiceClient


@pytest.mark.smoke
def test_notify_session_ok(
    notification_service_client: NotificationServiceClient,
) -> None:
    """POST /notify/session/:id с event возвращает 200."""
    session_id = str(uuid.uuid4())
    payload = {"event": "session.started", "payload": {"source": "qa"}}
    resp = notification_service_client.notify_session(session_id, payload)
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("ok") is True


@pytest.mark.negative
def test_notify_session_invalid_session_id(
    notification_service_client: NotificationServiceClient,
) -> None:
    """POST /notify/session/:id с невалидным UUID — 400."""
    payload = {"event": "test"}
    resp = notification_service_client.notify_session("not-a-uuid", payload)
    assert resp.status_code == 400


@pytest.mark.negative
def test_notify_session_missing_event(
    notification_service_client: NotificationServiceClient,
) -> None:
    """POST /notify/session/:id без event — 400."""
    session_id = str(uuid.uuid4())
    resp = notification_service_client.notify_session(session_id, {})
    assert resp.status_code == 400

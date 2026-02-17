"""Health/ready для data-channel-service."""

from __future__ import annotations

import pytest

from qa_tests.http_client import DataChannelServiceClient


@pytest.mark.smoke
def test_data_channel_health_ok(
    data_channel_service_client: DataChannelServiceClient,
) -> None:
    """GET /health возвращает 200 и service: data-channel-service."""
    resp = data_channel_service_client.health()
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("service") == "data-channel-service"


@pytest.mark.smoke
def test_data_channel_ready_ok(
    data_channel_service_client: DataChannelServiceClient,
) -> None:
    """GET /ready возвращает 200."""
    resp = data_channel_service_client.ready()
    assert resp.status_code == 200

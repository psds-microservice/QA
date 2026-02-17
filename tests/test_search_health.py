"""Health/ready для search-service."""

from __future__ import annotations

import pytest

from qa_tests.http_client import SearchServiceClient


@pytest.mark.smoke
def test_search_health_ok(search_service_client: SearchServiceClient) -> None:
    """GET /health возвращает 200 и service: search-service."""
    resp = search_service_client.health()
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("service") == "search-service"


@pytest.mark.smoke
def test_search_ready_ok(search_service_client: SearchServiceClient) -> None:
    """GET /ready возвращает 200."""
    resp = search_service_client.ready()
    assert resp.status_code == 200

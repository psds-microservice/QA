"""Health/ready для operator-pool-service."""

from __future__ import annotations

import pytest

from qa_tests.http_client import OperatorPoolServiceClient


@pytest.mark.smoke
def test_operator_pool_health_ok(
    operator_pool_service_client: OperatorPoolServiceClient,
) -> None:
    """GET /health возвращает 200 и service: operator-pool-service."""
    resp = operator_pool_service_client.health()
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("service") == "operator-pool-service"


@pytest.mark.smoke
def test_operator_pool_ready_ok(
    operator_pool_service_client: OperatorPoolServiceClient,
) -> None:
    """GET /ready возвращает 200."""
    resp = operator_pool_service_client.ready()
    assert resp.status_code == 200

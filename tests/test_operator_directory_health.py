"""Health/ready для operator-directory-service."""

from __future__ import annotations

import pytest

from qa_tests.http_client import OperatorDirectoryServiceClient


@pytest.mark.smoke
def test_operator_directory_health_ok(
    operator_directory_service_client: OperatorDirectoryServiceClient,
) -> None:
    """GET /health возвращает 200 и service: operator-directory-service."""
    resp = operator_directory_service_client.health()
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("service") == "operator-directory-service"


@pytest.mark.smoke
def test_operator_directory_ready_ok(
    operator_directory_service_client: OperatorDirectoryServiceClient,
) -> None:
    """GET /ready возвращает 200."""
    resp = operator_directory_service_client.ready()
    assert resp.status_code == 200

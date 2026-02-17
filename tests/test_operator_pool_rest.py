"""REST API operator-pool-service: /operator/status, next, stats, list."""

from __future__ import annotations

import uuid

import pytest

from qa_tests.http_client import OperatorPoolServiceClient


@pytest.mark.smoke
def test_operator_pool_list_ok(
    operator_pool_service_client: OperatorPoolServiceClient,
) -> None:
    """GET /operator/list возвращает 200 и operators — список."""
    resp = operator_pool_service_client.list_operators()
    assert resp.status_code == 200
    assert resp.json is not None
    operators = resp.json.get("operators")
    assert operators is None or isinstance(operators, list)


@pytest.mark.smoke
def test_operator_pool_stats_ok(
    operator_pool_service_client: OperatorPoolServiceClient,
) -> None:
    """GET /operator/stats возвращает 200, available и total."""
    resp = operator_pool_service_client.stats()
    assert resp.status_code == 200
    assert resp.json is not None
    assert "available" in resp.json
    assert "total" in resp.json


@pytest.mark.smoke
def test_operator_pool_next_empty_or_ok(
    operator_pool_service_client: OperatorPoolServiceClient,
) -> None:
    """GET /operator/next — 200 с operator_id или 404 если пул пуст."""
    resp = operator_pool_service_client.next_operator()
    assert resp.status_code in (200, 404)
    if resp.status_code == 200 and resp.json:
        assert "operatorId" in resp.json


@pytest.mark.smoke
def test_operator_pool_set_status_ok(
    operator_pool_service_client: OperatorPoolServiceClient,
) -> None:
    """POST /operator/status с валидным user_id, available, max_sessions — 200."""
    user_id = str(uuid.uuid4())
    payload = {"user_id": user_id, "available": True, "max_sessions": 2}
    resp = operator_pool_service_client.set_status(payload)
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("ok") is True


@pytest.mark.negative
def test_operator_pool_set_status_invalid_user_id(
    operator_pool_service_client: OperatorPoolServiceClient,
) -> None:
    """POST /operator/status с невалидным user_id — 400."""
    payload = {"user_id": "not-a-uuid", "available": True, "max_sessions": 1}
    resp = operator_pool_service_client.set_status(payload)
    assert resp.status_code == 400


@pytest.mark.negative
def test_operator_pool_set_status_invalid_body(
    operator_pool_service_client: OperatorPoolServiceClient,
) -> None:
    """POST /operator/status без обязательных полей — 400."""
    resp = operator_pool_service_client.set_status({})
    assert resp.status_code == 400

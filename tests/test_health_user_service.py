"""Health и readiness User Service."""

from __future__ import annotations

import allure
import pytest

from qa_tests.allure_utils import allure_step, link_jira, mark_feature, mark_severity, mark_story
from qa_tests.http_client import ApiGatewayClient
from qa_tests.metrics import measure_test_case


@pytest.mark.smoke
@allure.tag("health", "user-service")
def test_user_service_health(api_gateway_client: ApiGatewayClient) -> None:
    """GET /health возвращает 200."""
    mark_feature("User Service")
    mark_story("Health check")
    mark_severity("critical")
    link_jira("PSDS-100")

    with measure_test_case("test_user_service_health"):
        with allure_step("Запрос GET /health"):
            resp = api_gateway_client.get("/health")
        assert resp.status_code == 200


@pytest.mark.smoke
@allure.tag("health", "user-service")
def test_user_service_ready(api_gateway_client: ApiGatewayClient) -> None:
    """GET /ready возвращает 200."""
    mark_feature("User Service")
    mark_story("Readiness check")
    mark_severity("critical")
    link_jira("PSDS-100")

    with measure_test_case("test_user_service_ready"):
        with allure_step("Запрос GET /ready"):
            resp = api_gateway_client.get("/ready")
        assert resp.status_code == 200

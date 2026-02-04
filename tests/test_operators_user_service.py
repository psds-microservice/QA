"""Тесты операторов: доступные, статистика, доступность."""

from __future__ import annotations

import allure
import pytest

from qa_tests import data_factory
from qa_tests.allure_utils import allure_step, link_jira, mark_feature, mark_severity, mark_story
from qa_tests.http_client import ApiGatewayClient
from qa_tests.metrics import measure_test_case


@pytest.mark.smoke
@allure.tag("operators", "user-service")
def test_operators_available(api_gateway_client: ApiGatewayClient) -> None:
    """GET /operators/available возвращает список доступных операторов."""
    mark_feature("Operators")
    mark_story("Список доступных операторов")
    mark_severity("critical")
    link_jira("PSDS-301")

    with measure_test_case("test_operators_available"):
        with allure_step("Запрос GET /operators/available"):
            resp = api_gateway_client.operators_available(limit=10, offset=0)
        assert resp.status_code == 200
        assert resp.json is not None
        assert "operators" in resp.json
        assert "total" in resp.json


@pytest.mark.smoke
@allure.tag("operators", "user-service")
def test_operators_stats(api_gateway_client: ApiGatewayClient) -> None:
    """GET /operators/stats возвращает статистику операторов."""
    mark_feature("Operators")
    mark_story("Статистика операторов")
    mark_severity("normal")
    link_jira("PSDS-302")

    with measure_test_case("test_operators_stats"):
        resp = api_gateway_client.operators_stats()
        assert resp.status_code == 200
        assert resp.json is not None
        # API может вернуть список operators или агрегаты (rating, totalSessions и т.д.)
        assert "operators" in resp.json or "totalSessions" in resp.json or "rating" in resp.json


@pytest.mark.smoke
@allure.tag("operators", "user-service")
def test_operators_availability_authenticated(api_gateway_client: ApiGatewayClient) -> None:
    """PUT /operators/availability с токеном обновляет доступность оператора."""
    mark_feature("Operators")
    mark_story("Обновление доступности оператора")
    mark_severity("normal")
    link_jira("PSDS-303")

    with measure_test_case("test_operators_availability_authenticated"):
        payload = data_factory.build_user_registration()
        payload["role"] = "operator"
        api_gateway_client.register_user(payload)
        auth_resp = api_gateway_client.authenticate(
            {"email": payload["email"], "password": payload["password"]}
        )
        assert auth_resp.status_code == 200 and auth_resp.json
        token = auth_resp.json.get("accessToken") or auth_resp.json.get("access_token")

        with allure_step("Установка доступности"):
            resp = api_gateway_client.operators_availability(token, available=True)
        assert resp.status_code == 200
        assert resp.json is not None


@pytest.mark.negative
@allure.tag("operators", "user-service")
def test_operators_availability_unauthorized(api_gateway_client: ApiGatewayClient) -> None:
    """PUT /operators/availability без токена возвращает 401."""
    mark_feature("Operators")
    mark_story("Обновление доступности оператора")
    mark_severity("normal")
    link_jira("PSDS-402")

    with measure_test_case("test_operators_availability_unauthorized"):
        resp = api_gateway_client._request(
            "PUT",
            api_gateway_client._p("operators_availability"),
            json_body={"available": True},
            expected_status=None,
        )
        assert resp.status_code == 401

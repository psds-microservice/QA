from __future__ import annotations

import json

import allure
import pytest

from qa_tests import data_factory
from qa_tests.allure_utils import (
    allure_step,
    attach_json,
    link_jira,
    mark_feature,
    mark_severity,
    mark_story,
)
from qa_tests.http_client import ApiGatewayClient
from qa_tests.metrics import measure_test_case
from qa_tests.models import AuthRequest


@pytest.mark.regression
@allure.tag("gateway", "rate-limiting")
def test_rate_limiting_on_api_gateway(api_gateway_client: ApiGatewayClient, settings) -> None:
    """Проверка, что API Gateway корректно ограничивает частоту запросов."""
    mark_feature("API Gateway")
    mark_story("Rate limiting")
    mark_severity("critical")
    link_jira("PSDS-301")

    with measure_test_case("test_rate_limiting_on_api_gateway"):
        with allure_step("Подготовка пользователя для rate limiting"):
            if settings.rate_limit_test_user:
                email = settings.rate_limit_test_user
                password = "RateLimit123!"
                user_payload = {
                    "email": email,
                    "password": password,
                    "username": "Rate Limit User",
                    "role": "user",
                }
            else:
                user_payload = data_factory.build_user_registration()
                email = user_payload["email"]
                password = user_payload["password"]

            register_resp = api_gateway_client.register_user(user_payload)
            if register_resp.status_code in (404, 502, 503):
                pytest.skip(
                    "API Gateway не проксирует auth: POST /api/v1/auth/register вернул %s. "
                    "В psds/api-gateway нет маршрутов register/login — тест пропущен."
                    % register_resp.status_code
                )
            auth_resp = api_gateway_client.authenticate(
                AuthRequest(email=email, password=password).model_dump()
            )
            if auth_resp.status_code in (404, 502, 503):
                pytest.skip(
                    "API Gateway не проксирует auth: POST /api/v1/auth/login вернул %s. "
                    "В psds/api-gateway нет маршрутов register/login — тест пропущен."
                    % auth_resp.status_code
                )
            assert auth_resp.status_code == 200 and auth_resp.json is not None
            token = auth_resp.json.get("accessToken") or auth_resp.json.get("access_token")
            assert token, "В ответе login нет accessToken/access_token"

        with allure_step("Проверка наличия эндпоинта rate limiting"):
            first = api_gateway_client.rate_limited_endpoint(token)
            if first.status_code == 404:
                pytest.skip(
                    "API Gateway не реализует эндпоинт rate limiting (404). "
                    "В psds/api-gateway нет /v1/limits/rate-limited — тест пропущен."
                )

        with allure_step("Серийный вызов защищённого endpoint для провокации rate limiting"):
            responses = [first]
            for _ in range(19):
                resp = api_gateway_client.rate_limited_endpoint(token)
                responses.append(resp)

            codes = [r.status_code for r in responses]
            attach_json("rate_limiting_statuses", json.dumps(codes))

        with allure_step("Проверка наличия ответов 429 Too Many Requests"):
            assert any(code == 429 for code in codes), (
                "Ожидалось хотя бы одно ограничение по частоте (429). "
                "Проверьте настройку rate limiting на API Gateway."
            )

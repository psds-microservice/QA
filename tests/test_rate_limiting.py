from __future__ import annotations

import json

import allure
import pytest

from qa_tests import data_factory
from qa_tests.allure_utils import allure_step, attach_json, link_jira, mark_feature, mark_severity, mark_story
from qa_tests.http_client import ApiGatewayClient
from qa_tests.metrics import measure_test_case
from qa_tests.models import AuthRequest


@pytest.mark.regression
@allure.tag("gateway", "rate-limiting")
def test_rate_limiting_on_api_gateway(api_gateway_client: ApiGatewayClient, settings) -> None:  # type: ignore[no-untyped-def]
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
                    "full_name": "Rate Limit User",
                }
            else:
                user_payload = data_factory.build_user_registration()
                email = user_payload["email"]
                password = user_payload["password"]

            api_gateway_client.register_user(user_payload)
            auth_resp = api_gateway_client.authenticate(
                AuthRequest(email=email, password=password).model_dump()
            )
            assert auth_resp.status_code == 200 and auth_resp.json is not None
            token = auth_resp.json["access_token"]

        with allure_step("Серийный вызов защищённого endpoint для провокации rate limiting"):
            responses = []
            for _ in range(20):
                resp = api_gateway_client.rate_limited_endpoint(token)
                responses.append(resp)

            codes = [r.status_code for r in responses]
            attach_json("rate_limiting_statuses", json.dumps(codes))

        with allure_step("Проверка наличия ответов 429 Too Many Requests"):
            assert any(code == 429 for code in codes), "Ожидалось хотя бы одно ограничение по частоте (429)"


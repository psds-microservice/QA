from __future__ import annotations

import json

import allure
import pytest

from qa_tests import data_factory
from qa_tests.allure_utils import allure_step, attach_json, link_jira, mark_feature, mark_severity, mark_story
from qa_tests.http_client import ApiGatewayClient
from qa_tests.metrics import measure_test_case


@pytest.mark.negative
@allure.tag("validation", "user")
@pytest.mark.parametrize(
    "payload_builder,description",
    [
        (data_factory.build_invalid_registration_short_password, "слишком короткий пароль"),
        (data_factory.build_invalid_registration_bad_email, "некорректный email"),
    ],
)
def test_registration_input_validation_negative(
    api_gateway_client: ApiGatewayClient,
    payload_builder,
    description: str,
) -> None:
    """Негативные проверки валидации входных данных регистрации пользователя."""
    mark_feature("User Management")
    mark_story("Валидация входных данных")
    mark_severity("normal")
    link_jira("PSDS-401")

    test_name = f"test_registration_input_validation_negative[{description}]"
    with measure_test_case(test_name):
        with allure_step(f"Подготовка невалидных данных: {description}"):
            payload = payload_builder()
            attach_json("invalid_payload", json.dumps(payload, ensure_ascii=False, indent=2))

        with allure_step("Отправка запроса регистрации с невалидными данными"):
            resp = api_gateway_client.register_user(payload)
            attach_json("response_body", resp.raw.text)

        with allure_step("Проверка кода ответа и структуры ошибки"):
            # В большинстве REST API для ошибок валидации используется 400
            assert resp.status_code in {400, 422}
            if resp.json:
                assert "code" in resp.json or "errors" in resp.json


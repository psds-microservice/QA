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
        (data_factory.build_invalid_registration_invalid_role, "недопустимая роль"),
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
            assert resp.status_code in {400, 422}
            if resp.json:
                assert "code" in resp.json or "errors" in resp.json or "message" in resp.json


@pytest.mark.negative
@allure.tag("validation", "auth")
@pytest.mark.parametrize(
    "payload_builder,description",
    [
        (data_factory.build_invalid_login_empty_email, "пустой email"),
        (data_factory.build_invalid_login_empty_password, "пустой пароль"),
    ],
)
def test_login_validation_negative(
    api_gateway_client: ApiGatewayClient,
    payload_builder,
    description: str,
) -> None:
    """Негативные проверки валидации login."""
    mark_feature("User Management")
    mark_story("Валидация login")
    mark_severity("normal")
    link_jira("PSDS-401")

    with measure_test_case(f"test_login_validation_negative[{description}]"):
        payload = payload_builder()
        attach_json("invalid_payload", json.dumps(payload, ensure_ascii=False, indent=2))
        resp = api_gateway_client.authenticate(payload)
        assert resp.status_code in {400, 422}


@pytest.mark.negative
@allure.tag("validation", "auth")
def test_login_invalid_credentials(api_gateway_client: ApiGatewayClient) -> None:
    """Логин с неверным паролем возвращает 401."""
    mark_feature("User Management")
    mark_story("Неверные учётные данные")
    mark_severity("normal")
    link_jira("PSDS-401")

    with measure_test_case("test_login_invalid_credentials"):
        payload = data_factory.build_user_registration()
        api_gateway_client.register_user(payload)
        wrong_login = {"email": payload["email"], "password": "wrong-password"}
        resp = api_gateway_client.authenticate(wrong_login)
        assert resp.status_code == 401


@pytest.mark.negative
@allure.tag("validation", "auth")
def test_refresh_validation_negative(api_gateway_client: ApiGatewayClient) -> None:
    """Refresh с пустым refresh_token возвращает 400 или 401."""
    mark_feature("User Management")
    mark_story("Валидация refresh")
    mark_severity("normal")
    link_jira("PSDS-401")

    with measure_test_case("test_refresh_validation_negative"):
        payload = data_factory.build_invalid_refresh_empty()
        resp = api_gateway_client.auth_refresh(payload)
        assert resp.status_code in {400, 401, 422}


@pytest.mark.negative
@allure.tag("validation", "auth")
def test_refresh_invalid_token(api_gateway_client: ApiGatewayClient) -> None:
    """Refresh с невалидным/поддельным refresh_token возвращает 401."""
    mark_feature("User Management")
    mark_story("Невалидный refresh token")
    mark_severity("normal")
    link_jira("PSDS-401")

    with measure_test_case("test_refresh_invalid_token"):
        resp = api_gateway_client._request(
            "POST",
            api_gateway_client._p("auth_refresh"),
            json_body={"refresh_token": "invalid-or-expired-token"},
            expected_status=None,
        )
        assert resp.status_code == 401


@pytest.mark.negative
@allure.tag("validation", "auth")
def test_logout_without_token(api_gateway_client: ApiGatewayClient) -> None:
    """Logout без токена — сервис может вернуть 200/204 или 401."""
    mark_feature("User Management")
    mark_story("Logout без авторизации")
    mark_severity("normal")
    link_jira("PSDS-401")

    with measure_test_case("test_logout_without_token"):
        resp = api_gateway_client._request(
            "POST",
            api_gateway_client._p("auth_logout"),
            expected_status=None,
        )
        assert resp.status_code in (200, 204, 401)


@pytest.mark.negative
@allure.tag("validation", "auth")
def test_register_duplicate_email(api_gateway_client: ApiGatewayClient) -> None:
    """Регистрация с уже существующим email возвращает 400 или 409."""
    mark_feature("User Management")
    mark_story("Дубликат email при регистрации")
    mark_severity("normal")
    link_jira("PSDS-401")

    with measure_test_case("test_register_duplicate_email"):
        payload = data_factory.build_user_registration()
        api_gateway_client.register_user(payload)
        second_payload = {
            "username": "OtherUser",
            "email": payload["email"],
            "password": "anotherpass123",
            "role": "client",
        }
        resp = api_gateway_client.register_user(second_payload)
        assert resp.status_code in (400, 409)


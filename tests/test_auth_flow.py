from __future__ import annotations

import json

import allure
import pytest

from qa_tests import data_factory
from qa_tests.allure_utils import allure_step, attach_json, link_jira, mark_feature, mark_severity, mark_story
from qa_tests.http_client import ApiGatewayClient
from qa_tests.metrics import measure_test_case
from qa_tests.models import AuthRequest, AuthResponse


@pytest.mark.smoke
@allure.tag("auth", "user")
def test_user_registration_and_authentication(api_gateway_client: ApiGatewayClient) -> None:
    """Регистрация и последующая аутентификация пользователя (User Service: /api/v1/auth/register, login)."""
    mark_feature("User Management")
    mark_story("Регистрация и аутентификация пользователя")
    mark_severity("critical")
    link_jira("PSDS-101")

    with measure_test_case("test_user_registration_and_authentication"):
        # Регистрация (payload: username, email, password, role)
        with allure_step("Генерация данных пользователя"):
            payload = data_factory.build_user_registration()
            attach_json("registration_payload", json.dumps(payload, ensure_ascii=False, indent=2))

        with allure_step("Отправка запроса регистрации"):
            resp = api_gateway_client.register_user(payload)
            assert resp.status_code in (200, 201), f"Unexpected status code: {resp.status_code}"
            assert resp.json is not None, "Registration response has no JSON body"
            attach_json("registration_response", json.dumps(resp.json, ensure_ascii=False, indent=2))

        with allure_step("Проверка структуры ответа регистрации (токены)"):
            tokens = AuthResponse.model_validate(resp.json)
            assert tokens.access_token

        # Аутентификация
        with allure_step("Аутентификация зарегистрированного пользователя"):
            auth_req = AuthRequest(email=payload["email"], password=payload["password"])
            auth_resp = api_gateway_client.authenticate(auth_req.model_dump())
            assert auth_resp.status_code == 200
            assert auth_resp.json is not None
            attach_json("auth_response", json.dumps(auth_resp.json, ensure_ascii=False, indent=2))

        with allure_step("Проверка структуры токенов"):
            auth_tokens = AuthResponse.model_validate(auth_resp.json)
            assert auth_tokens.access_token
            assert auth_tokens.token_type.lower() == "bearer"

        # Refresh токена
        with allure_step("Обновление токена через refresh"):
            refresh_payload = {"refresh_token": auth_tokens.refresh_token or ""}
            assert refresh_payload["refresh_token"], "refresh_token должен быть в ответе login"
            refresh_resp = api_gateway_client.auth_refresh(refresh_payload)
            assert refresh_resp.status_code == 200
            assert refresh_resp.json and "accessToken" in refresh_resp.json

        # Logout
        with allure_step("Выход (logout)"):
            logout_resp = api_gateway_client.auth_logout(auth_tokens.access_token)
            assert logout_resp.status_code in (200, 204)


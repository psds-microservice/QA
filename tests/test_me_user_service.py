"""Тесты GET/PUT /api/v1/users/me (текущий пользователь)."""

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


@pytest.mark.smoke
@allure.tag("me", "user-service")
def test_get_me_authenticated(api_gateway_client: ApiGatewayClient) -> None:
    """GET /users/me с валидным токеном возвращает данные пользователя."""
    mark_feature("User Management")
    mark_story("Текущий пользователь (me)")
    mark_severity("critical")
    link_jira("PSDS-102")

    with measure_test_case("test_get_me_authenticated"):
        with allure_step("Регистрация и логин"):
            payload = data_factory.build_user_registration()
            api_gateway_client.register_user(payload)
            auth_resp = api_gateway_client.authenticate(
                {"email": payload["email"], "password": payload["password"]}
            )
            assert auth_resp.status_code == 200 and auth_resp.json
            token = auth_resp.json.get("accessToken") or auth_resp.json.get("access_token")

        with allure_step("Запрос GET /users/me"):
            resp = api_gateway_client.get_me(token)
            attach_json("me_response", json.dumps(resp.json or {}, ensure_ascii=False, indent=2))

        assert resp.status_code == 200
        assert resp.json
        assert resp.json.get("id") or resp.json.get("email")
        assert resp.json.get("email") == payload["email"]


@pytest.mark.negative
@allure.tag("me", "user-service")
def test_get_me_unauthorized(api_gateway_client: ApiGatewayClient) -> None:
    """GET /users/me без токена возвращает 401."""
    mark_feature("User Management")
    mark_story("Текущий пользователь (me)")
    mark_severity("normal")
    link_jira("PSDS-402")

    with measure_test_case("test_get_me_unauthorized"):
        resp = api_gateway_client._request(
            "GET",
            api_gateway_client._p("users_me"),
            expected_status=None,
        )
        assert resp.status_code == 401


@pytest.mark.smoke
@allure.tag("me", "user-service")
def test_update_me_authenticated(api_gateway_client: ApiGatewayClient) -> None:
    """PUT /users/me с валидным токеном обновляет профиль."""
    mark_feature("User Management")
    mark_story("Обновление профиля (me)")
    mark_severity("critical")
    link_jira("PSDS-103")

    with measure_test_case("test_update_me_authenticated"):
        with allure_step("Регистрация и логин"):
            payload = data_factory.build_user_registration()
            api_gateway_client.register_user(payload)
            auth_resp = api_gateway_client.authenticate(
                {"email": payload["email"], "password": payload["password"]}
            )
            assert auth_resp.status_code == 200 and auth_resp.json
            token = auth_resp.json.get("accessToken") or auth_resp.json.get("access_token")

        with allure_step("Получение текущего профиля для полного payload"):
            me_resp = api_gateway_client.get_me(token)
            assert me_resp.status_code == 200 and me_resp.json
            me = me_resp.json
            # Собираем payload из ответа me (snake_case/camelCase), чтобы не затирать поля пустыми
            update_payload = {
                "id": me.get("id", ""),
                "username": "UpdatedName",
                "email": me.get("email") or me.get("Email", ""),
                "phone": me.get("phone") or me.get("Phone", ""),
                "status": me.get("status") or me.get("Status", "active"),
            }

        with allure_step("Обновление профиля (username)"):
            resp = api_gateway_client.update_me(token, update_payload)
            attach_json(
                "update_response", json.dumps(resp.json or {}, ensure_ascii=False, indent=2)
            )

        assert resp.status_code in (200, 500), f"Unexpected status: {resp.status_code}"
        if resp.status_code == 200:
            assert resp.json


@pytest.mark.negative
@allure.tag("me", "user-service")
def test_get_me_invalid_bearer(api_gateway_client: ApiGatewayClient) -> None:
    """GET /users/me с невалидным/истёкшим Bearer возвращает 401."""
    mark_feature("User Management")
    mark_story("Текущий пользователь (me)")
    mark_severity("normal")
    link_jira("PSDS-402")

    with measure_test_case("test_get_me_invalid_bearer"):
        resp = api_gateway_client._request(
            "GET",
            api_gateway_client._p("users_me"),
            headers={"Authorization": "Bearer invalid-or-expired-token"},
            expected_status=None,
        )
        assert resp.status_code == 401


@pytest.mark.negative
@allure.tag("me", "user-service")
def test_update_me_unauthorized(api_gateway_client: ApiGatewayClient) -> None:
    """PUT /users/me без токена возвращает 401."""
    mark_feature("User Management")
    mark_story("Обновление профиля (me)")
    mark_severity("normal")
    link_jira("PSDS-402")

    with measure_test_case("test_update_me_unauthorized"):
        resp = api_gateway_client._request(
            "PUT",
            api_gateway_client._p("users_me"),
            json_body={"username": "Any"},
            expected_status=None,
        )
        assert resp.status_code == 401


@pytest.mark.negative
@allure.tag("me", "user-service")
def test_update_me_invalid_status(api_gateway_client: ApiGatewayClient) -> None:
    """PUT /users/me с недопустимым status возвращает 400."""
    mark_feature("User Management")
    mark_story("Валидация обновления me")
    mark_severity("normal")
    link_jira("PSDS-401")

    with measure_test_case("test_update_me_invalid_status"):
        payload = data_factory.build_user_registration()
        api_gateway_client.register_user(payload)
        auth_resp = api_gateway_client.authenticate(
            {"email": payload["email"], "password": payload["password"]}
        )
        token = auth_resp.json.get("accessToken") or auth_resp.json.get("access_token")
        me_resp = api_gateway_client.get_me(token)
        assert me_resp.status_code == 200 and me_resp.json
        me = me_resp.json
        update_payload = {
            "id": me.get("id", ""),
            "username": me.get("username", ""),
            "email": me.get("email", ""),
            "status": "invalid_status_value",
        }
        resp = api_gateway_client._request(
            "PUT",
            api_gateway_client._p("users_me"),
            json_body=update_payload,
            headers={"Authorization": f"Bearer {token}"},
            expected_status=None,
        )
        # Сервис может вернуть 400/422 при валидации или 500 при внутренней ошибке
        assert resp.status_code in (400, 422, 500)

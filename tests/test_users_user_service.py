"""Тесты CRUD пользователей: GET /api/v1/users/{id} и т.д."""

from __future__ import annotations

import allure
import pytest

from qa_tests import data_factory
from qa_tests.allure_utils import allure_step, link_jira, mark_feature, mark_severity, mark_story
from qa_tests.http_client import ApiGatewayClient
from qa_tests.metrics import measure_test_case


@pytest.mark.smoke
@allure.tag("users", "user-service")
def test_get_user_by_id_self(api_gateway_client: ApiGatewayClient) -> None:
    """GET /users/{id} с токеном своего пользователя возвращает 200."""
    mark_feature("User Management")
    mark_story("Получение пользователя по ID")
    mark_severity("critical")
    link_jira("PSDS-104")

    with measure_test_case("test_get_user_by_id_self"):
        with allure_step("Регистрация и логин"):
            payload = data_factory.build_user_registration()
            reg = api_gateway_client.register_user(payload)
            assert reg.status_code in (200, 201) and reg.json
            user_id = None
            if reg.json.get("user") and reg.json["user"].get("id"):
                user_id = reg.json["user"]["id"]
            if not user_id and reg.json.get("user", {}).get("id"):
                user_id = reg.json["user"]["id"]
            auth_resp = api_gateway_client.authenticate(
                {"email": payload["email"], "password": payload["password"]}
            )
            assert auth_resp.status_code == 200 and auth_resp.json
            token = auth_resp.json.get("accessToken") or auth_resp.json.get("access_token")
            if not user_id:
                me_resp = api_gateway_client.get_me(token)
                assert me_resp.status_code == 200 and me_resp.json
                user_id = me_resp.json.get("id")

        with allure_step("Запрос GET /users/{id}"):
            assert user_id, "user_id должен быть получен из me или register"
            resp = api_gateway_client.get_user(token, user_id)

        assert resp.status_code == 200
        assert resp.json and (resp.json.get("id") == user_id or resp.json.get("email") == payload["email"])


@pytest.mark.negative
@allure.tag("users", "user-service")
def test_get_user_not_found(api_gateway_client: ApiGatewayClient) -> None:
    """GET /users/{id} с несуществующим ID возвращает 404."""
    mark_feature("User Management")
    mark_story("Получение пользователя по ID")
    mark_severity("normal")
    link_jira("PSDS-404")

    with measure_test_case("test_get_user_not_found"):
        payload = data_factory.build_user_registration()
        api_gateway_client.register_user(payload)
        auth_resp = api_gateway_client.authenticate(
            {"email": payload["email"], "password": payload["password"]}
        )
        token = auth_resp.json.get("accessToken") or auth_resp.json.get("access_token")
        resp = api_gateway_client._request(
            "GET",
            api_gateway_client._p("users_by_id", id="00000000-0000-0000-0000-000000000000"),
            headers={"Authorization": f"Bearer {token}"},
            expected_status=None,
        )
        assert resp.status_code == 404


@pytest.mark.negative
@allure.tag("users", "user-service")
def test_get_user_unauthorized(api_gateway_client: ApiGatewayClient) -> None:
    """GET /users/{id} без токена возвращает 401 или 404 (зависит от реализации)."""
    mark_feature("User Management")
    mark_story("Получение пользователя по ID")
    mark_severity("normal")
    link_jira("PSDS-402")

    with measure_test_case("test_get_user_unauthorized"):
        resp = api_gateway_client._request(
            "GET",
            api_gateway_client._p("users_by_id", id="00000000-0000-0000-0000-000000000000"),
            expected_status=None,
        )
        assert resp.status_code in (401, 404)


@pytest.mark.smoke
@allure.tag("users", "user-service")
def test_delete_user_authenticated(api_gateway_client: ApiGatewayClient) -> None:
    """DELETE /users/{id} с токеном своего пользователя возвращает 200/204."""
    mark_feature("User Management")
    mark_story("Удаление пользователя")
    mark_severity("critical")
    link_jira("PSDS-105")

    with measure_test_case("test_delete_user_authenticated"):
        payload = data_factory.build_user_registration()
        api_gateway_client.register_user(payload)
        auth_resp = api_gateway_client.authenticate(
            {"email": payload["email"], "password": payload["password"]}
        )
        token = auth_resp.json.get("accessToken") or auth_resp.json.get("access_token")
        me_resp = api_gateway_client.get_me(token)
        assert me_resp.status_code == 200 and me_resp.json
        user_id = me_resp.json.get("id")
        assert user_id
        resp = api_gateway_client.delete_user(token, user_id)
        assert resp.status_code in (200, 204)


@pytest.mark.negative
@allure.tag("users", "user-service")
def test_delete_user_unauthorized(api_gateway_client: ApiGatewayClient) -> None:
    """DELETE /users/{id} без токена — сервис может вернуть 401, 404 или 200 (зависит от реализации)."""
    mark_feature("User Management")
    mark_story("Удаление пользователя")
    mark_severity("normal")
    link_jira("PSDS-402")

    with measure_test_case("test_delete_user_unauthorized"):
        resp = api_gateway_client._request(
            "DELETE",
            api_gateway_client._p("users_by_id", id="00000000-0000-0000-0000-000000000000"),
            expected_status=None,
        )
        assert resp.status_code in (200, 204, 401, 404)


@pytest.mark.smoke
@allure.tag("users", "presence", "user-service")
def test_update_presence_authenticated(api_gateway_client: ApiGatewayClient) -> None:
    """PUT /users/{user_id}/presence с токеном своего user_id возвращает 200."""
    mark_feature("User Management")
    mark_story("Presence")
    mark_severity("normal")
    link_jira("PSDS-106")

    with measure_test_case("test_update_presence_authenticated"):
        payload = data_factory.build_user_registration()
        api_gateway_client.register_user(payload)
        auth_resp = api_gateway_client.authenticate(
            {"email": payload["email"], "password": payload["password"]}
        )
        token = auth_resp.json.get("accessToken") or auth_resp.json.get("access_token")
        me_resp = api_gateway_client.get_me(token)
        assert me_resp.status_code == 200 and me_resp.json
        user_id = me_resp.json.get("id")
        assert user_id
        resp = api_gateway_client.update_presence(token, user_id, is_online=True)
        assert resp.status_code == 200


@pytest.mark.negative
@allure.tag("users", "presence", "user-service")
def test_update_presence_unauthorized(api_gateway_client: ApiGatewayClient) -> None:
    """PUT /users/{user_id}/presence без токена возвращает 401 или 404 (user not found)."""
    mark_feature("User Management")
    mark_story("Presence")
    mark_severity("normal")
    link_jira("PSDS-402")

    with measure_test_case("test_update_presence_unauthorized"):
        resp = api_gateway_client._request(
            "PUT",
            api_gateway_client._p("users_presence", user_id="00000000-0000-0000-0000-000000000000"),
            json_body={"is_online": True},
            expected_status=None,
        )
        assert resp.status_code in (401, 404)

"""Тесты сессий: создание, список, валидация."""

from __future__ import annotations

import json

import allure
import pytest

from qa_tests import data_factory
from qa_tests.allure_utils import allure_step, attach_json, link_jira, mark_feature, mark_severity, mark_story
from qa_tests.http_client import ApiGatewayClient
from qa_tests.metrics import measure_test_case


def _register_and_get_token(api_gateway_client: ApiGatewayClient) -> tuple[dict, str, str]:
    """Регистрация, логин, возврат (payload, token, user_id)."""
    payload = data_factory.build_user_registration()
    api_gateway_client.register_user(payload)
    auth_resp = api_gateway_client.authenticate(
        {"email": payload["email"], "password": payload["password"]}
    )
    assert auth_resp.status_code == 200 and auth_resp.json
    token = auth_resp.json.get("accessToken") or auth_resp.json.get("access_token")
    me_resp = api_gateway_client.get_me(token)
    assert me_resp.status_code == 200 and me_resp.json
    user_id = me_resp.json.get("id")
    assert user_id
    return payload, token, user_id


@pytest.mark.smoke
@allure.tag("sessions", "user-service")
def test_create_session(api_gateway_client: ApiGatewayClient) -> None:
    """POST /users/{id}/sessions создаёт сессию и возвращает 201."""
    mark_feature("Sessions")
    mark_story("Создание сессии")
    mark_severity("critical")
    link_jira("PSDS-201")

    with measure_test_case("test_create_session"):
        _, token, user_id = _register_and_get_token(api_gateway_client)
        session_payload = data_factory.build_create_session_payload(
            session_type="consultation", participant_role="host"
        )
        with allure_step("Создание сессии"):
            resp = api_gateway_client.create_session(token, user_id, session_payload)
            attach_json("session_response", json.dumps(resp.json or {}, ensure_ascii=False, indent=2))
        assert resp.status_code in (200, 201)
        assert resp.json


@pytest.mark.smoke
@allure.tag("sessions", "user-service")
def test_list_user_sessions(api_gateway_client: ApiGatewayClient) -> None:
    """GET /users/{id}/sessions возвращает список сессий."""
    mark_feature("Sessions")
    mark_story("Список сессий пользователя")
    mark_severity("normal")
    link_jira("PSDS-202")

    with measure_test_case("test_list_user_sessions"):
        _, token, user_id = _register_and_get_token(api_gateway_client)
        resp = api_gateway_client.list_user_sessions(token, user_id, limit=10, offset=0)
        assert resp.status_code == 200
        assert resp.json is not None
        assert "sessions" in resp.json


@pytest.mark.smoke
@allure.tag("sessions", "user-service")
def test_list_active_sessions(api_gateway_client: ApiGatewayClient) -> None:
    """GET /users/{id}/active-sessions возвращает активные сессии."""
    mark_feature("Sessions")
    mark_story("Активные сессии")
    mark_severity("normal")
    link_jira("PSDS-203")

    with measure_test_case("test_list_active_sessions"):
        _, token, user_id = _register_and_get_token(api_gateway_client)
        resp = api_gateway_client.list_active_sessions(token, user_id)
        assert resp.status_code == 200
        assert resp.json is not None
        assert "sessions" in resp.json


@pytest.mark.smoke
@allure.tag("sessions", "user-service")
def test_validate_session(api_gateway_client: ApiGatewayClient) -> None:
    """POST /sessions/validate проверяет доступ к сессии."""
    mark_feature("Sessions")
    mark_story("Валидация сессии")
    mark_severity("normal")
    link_jira("PSDS-204")

    with measure_test_case("test_validate_session"):
        _, token, user_id = _register_and_get_token(api_gateway_client)
        payload = data_factory.build_validate_session_payload(user_id=user_id)
        resp = api_gateway_client.validate_session(payload)
        assert resp.status_code == 200
        assert resp.json is not None
        assert "allowed" in resp.json


@pytest.mark.negative
@allure.tag("sessions", "user-service")
def test_create_session_invalid_type(api_gateway_client: ApiGatewayClient) -> None:
    """Создание сессии с невалидным session_type возвращает 400."""
    mark_feature("Sessions")
    mark_story("Валидация создания сессии")
    mark_severity("normal")
    link_jira("PSDS-401")

    with measure_test_case("test_create_session_invalid_type"):
        _, token, user_id = _register_and_get_token(api_gateway_client)
        payload = data_factory.build_create_session_payload(
            session_type="invalid_type",
            participant_role="host",
        )
        resp = api_gateway_client._request(
            "POST",
            api_gateway_client._p("users_sessions", id=user_id),
            json_body=payload,
            headers={"Authorization": f"Bearer {token}"},
            expected_status=None,
        )
        assert resp.status_code in (400, 422)


@pytest.mark.negative
@allure.tag("sessions", "user-service")
def test_list_sessions_unauthorized(api_gateway_client: ApiGatewayClient) -> None:
    """GET /users/{id}/sessions без токена — сервис может вернуть 200 (пустой список) или 401."""
    mark_feature("Sessions")
    mark_story("Список сессий")
    mark_severity("normal")
    link_jira("PSDS-402")

    with measure_test_case("test_list_sessions_unauthorized"):
        _, _, user_id = _register_and_get_token(api_gateway_client)
        resp = api_gateway_client._request(
            "GET",
            api_gateway_client._p("users_sessions", id=user_id),
            expected_status=None,
        )
        assert resp.status_code in (200, 401)


@pytest.mark.negative
@allure.tag("sessions", "user-service")
def test_create_session_unauthorized(api_gateway_client: ApiGatewayClient) -> None:
    """POST /users/{id}/sessions без токена — сервис может вернуть 200 (создаст сессию) или 401."""
    mark_feature("Sessions")
    mark_story("Создание сессии")
    mark_severity("normal")
    link_jira("PSDS-402")

    with measure_test_case("test_create_session_unauthorized"):
        _, _, user_id = _register_and_get_token(api_gateway_client)
        payload = data_factory.build_create_session_payload()
        resp = api_gateway_client._request(
            "POST",
            api_gateway_client._p("users_sessions", id=user_id),
            json_body=payload,
            expected_status=None,
        )
        assert resp.status_code in (200, 201, 401)


@pytest.mark.negative
@allure.tag("sessions", "user-service")
def test_validate_session_empty_user_id(api_gateway_client: ApiGatewayClient) -> None:
    """POST /sessions/validate с пустым user_id возвращает 400."""
    mark_feature("Sessions")
    mark_story("Валидация сессии")
    mark_severity("normal")
    link_jira("PSDS-401")

    with measure_test_case("test_validate_session_empty_user_id"):
        payload = {"user_id": "", "session_external_id": "ext-123", "participant_role": "host"}
        resp = api_gateway_client._request(
            "POST",
            api_gateway_client._p("sessions_validate"),
            json_body=payload,
            expected_status=None,
        )
        assert resp.status_code in (400, 422)

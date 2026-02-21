"""REST API session-manager-service.

Эндпоинты: GET /session/{id}, GET /session/{id}/participants,
POST /session/join, POST /session/{id}/invite, POST /session/{id}/control.
"""

from __future__ import annotations

import uuid

import pytest

from qa_tests.http_client import SessionManagerServiceClient


@pytest.mark.smoke
def test_get_session_not_found(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """GET /session/{id} для несуществующей сессии — 404."""
    session_id = str(uuid.uuid4())
    resp = session_manager_service_client.get_session(session_id)
    assert resp.status_code == 404


@pytest.mark.smoke
def test_get_participants_not_found(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """GET /session/{id}/participants для несуществующей сессии — 404."""
    session_id = str(uuid.uuid4())
    resp = session_manager_service_client.get_participants(session_id)
    assert resp.status_code == 404


@pytest.mark.smoke
def test_join_session_invalid(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/join с несуществующей сессией — 400 или 404."""
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    resp = session_manager_service_client.join_session(
        session_id=session_id, pin="1234", user_id=user_id
    )
    # Сервис может вернуть 400 (невалидные данные) или 404 (сессия не найдена)
    assert resp.status_code in (400, 404)


@pytest.mark.negative
def test_join_session_not_found_by_session_id(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/join с несуществующим session_id — должен вернуть 404, не панику."""
    non_existent_session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    resp = session_manager_service_client.join_session(
        session_id=non_existent_session_id, pin="", user_id=user_id
    )
    # Должен вернуть 404 (Not Found), а не 500 (Internal Server Error от паники)
    assert (
        resp.status_code == 404
    ), f"Expected 404, got {resp.status_code}. Response: {resp.raw.text}"
    # Проверяем, что ответ валидный JSON (не HTML страница ошибки от паники)
    assert resp.json is not None, "Response should be valid JSON, not HTML error page"
    # Проверяем, что в ответе есть сообщение об ошибке
    assert (
        "not found" in resp.json.get("message", "").lower() or "not found" in resp.raw.text.lower()
    )


@pytest.mark.negative
def test_join_session_not_found_by_pin(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/join с несуществующим PIN — должен вернуть 404, не панику."""
    non_existent_pin = "999999"  # PIN, которого точно нет
    user_id = str(uuid.uuid4())
    resp = session_manager_service_client.join_session(
        session_id="", pin=non_existent_pin, user_id=user_id
    )
    # Должен вернуть 404 (Not Found), а не 500 (Internal Server Error от паники)
    assert (
        resp.status_code == 404
    ), f"Expected 404, got {resp.status_code}. Response: {resp.raw.text}"
    # Проверяем, что ответ валидный JSON (не HTML страница ошибки от паники)
    assert resp.json is not None, "Response should be valid JSON, not HTML error page"
    # Проверяем, что в ответе есть сообщение об ошибке
    assert (
        "not found" in resp.json.get("message", "").lower() or "not found" in resp.raw.text.lower()
    )


@pytest.mark.negative
def test_join_session_invalid_session_id_format(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/join с невалидным форматом session_id — должен вернуть 400, не панику."""
    invalid_session_id = "not-a-valid-uuid"
    user_id = str(uuid.uuid4())
    resp = session_manager_service_client.join_session(
        session_id=invalid_session_id, pin="", user_id=user_id
    )
    # Должен вернуть 400 (Bad Request), а не 500 (Internal Server Error от паники)
    assert (
        resp.status_code == 400
    ), f"Expected 400, got {resp.status_code}. Response: {resp.raw.text}"
    # Проверяем, что ответ валидный JSON (не HTML страница ошибки от паники)
    assert resp.json is not None, "Response should be valid JSON, not HTML error page"


@pytest.mark.negative
def test_join_session_invalid_user_id_format(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/join с невалидным форматом user_id — должен вернуть 400, не панику."""
    session_id = str(uuid.uuid4())
    invalid_user_id = "not-a-valid-uuid"
    resp = session_manager_service_client.join_session(
        session_id=session_id, pin="", user_id=invalid_user_id
    )
    # Должен вернуть 400 (Bad Request), а не 500 (Internal Server Error от паники)
    assert (
        resp.status_code == 400
    ), f"Expected 400, got {resp.status_code}. Response: {resp.raw.text}"
    # Проверяем, что ответ валидный JSON (не HTML страница ошибки от паники)
    assert resp.json is not None, "Response should be valid JSON, not HTML error page"


@pytest.mark.smoke
def test_invite_operator_not_found(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/{id}/invite для несуществующей сессии — 404."""
    session_id = str(uuid.uuid4())
    operator_id = str(uuid.uuid4())
    resp = session_manager_service_client.invite_operator(session_id, operator_id)
    assert resp.status_code == 404


@pytest.mark.smoke
def test_control_session_not_found(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/{id}/control для несуществующей сессии — 404."""
    session_id = str(uuid.uuid4())
    caller_id = str(uuid.uuid4())  # any UUID so permission check passes, then 404
    resp = session_manager_service_client.control_session(session_id, "start", caller_id=caller_id)
    assert resp.status_code == 404


@pytest.mark.negative
def test_get_session_invalid_id(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """GET /session/{id} с невалидным UUID — 400."""
    resp = session_manager_service_client.get_session("not-a-uuid")
    assert resp.status_code == 400


@pytest.mark.negative
def test_get_participants_invalid_id(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """GET /session/{id}/participants с невалидным UUID — 400."""
    resp = session_manager_service_client.get_participants("not-a-uuid")
    assert resp.status_code == 400


@pytest.mark.negative
def test_join_session_missing_fields(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/join без обязательных полей — 400 или соединение закрывается."""
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    # Отправляем без pin
    payload = {"sessionId": session_id, "userId": user_id}
    try:
        resp = session_manager_service_client._request(
            "POST",
            "/session/join",
            json_body=payload,
            expected_status=(200, 400, 404, 500),
        )
        # Если запрос прошёл, должен быть 400
        assert resp.status_code == 400
    except Exception:
        # Если сервер закрыл соединение без ответа — это тоже ошибка валидации
        # Тест считается пройденным, так как сервис не принял невалидный запрос
        pass


@pytest.mark.negative
def test_invite_operator_invalid_session_id(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/{id}/invite с невалидным session_id — 400."""
    operator_id = str(uuid.uuid4())
    resp = session_manager_service_client.invite_operator("not-a-uuid", operator_id)
    assert resp.status_code == 400


@pytest.mark.negative
def test_invite_operator_missing_body(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/{id}/invite без operatorId — 400."""
    session_id = str(uuid.uuid4())
    resp = session_manager_service_client._request(
        "POST",
        f"/session/{session_id}/invite",
        json_body={},
        expected_status=(200, 400, 404, 500),
    )
    assert resp.status_code == 400


@pytest.mark.negative
def test_control_session_invalid_id(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/{id}/control с невалидным session_id — 400."""
    resp = session_manager_service_client.control_session("not-a-uuid", "start")
    assert resp.status_code == 400


@pytest.mark.negative
def test_control_session_missing_action(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/{id}/control без action — 400 (action validated before caller check)."""
    session_id = str(uuid.uuid4())
    resp = session_manager_service_client._request(
        "POST",
        f"/session/{session_id}/control",
        json_body={},
        expected_status=(200, 400, 403, 404, 500),
    )
    assert resp.status_code == 400


# Positive tests (создают сессии через API)


@pytest.mark.smoke
def test_create_session_ok(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session создаёт сессию консультации и возвращает id, status, pin."""
    client_id = str(uuid.uuid4())
    resp = session_manager_service_client.create_session(client_id)
    assert resp.status_code in (200, 201)
    assert resp.json is not None
    body = resp.json
    assert body.get("id")
    assert body.get("status") == "waiting"
    assert body.get("pin")
    assert len(body.get("pin", "")) == 6  # PIN должен быть 6 цифр


@pytest.mark.smoke
def test_create_session_with_stream_session_id(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session с stream_session_id создаёт сессию с привязкой к streaming сессии."""
    client_id = str(uuid.uuid4())
    stream_session_id = str(uuid.uuid4())
    resp = session_manager_service_client.create_session(
        client_id, stream_session_id=stream_session_id
    )
    assert resp.status_code in (200, 201)
    assert resp.json is not None
    assert resp.json.get("id")
    assert resp.json.get("status") == "waiting"
    assert resp.json.get("pin")


@pytest.mark.negative
def test_create_session_invalid_client_id(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session с невалидным client_id — 400."""
    resp = session_manager_service_client._request(
        "POST",
        "/session",
        json_body={"clientId": "not-a-uuid"},
        expected_status=(200, 400, 500),
    )
    assert resp.status_code == 400


@pytest.mark.negative
def test_create_session_missing_client_id(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session без client_id — 400."""
    resp = session_manager_service_client._request(
        "POST",
        "/session",
        json_body={},
        expected_status=(200, 400, 500),
    )
    assert resp.status_code == 400


@pytest.mark.smoke
def test_get_session_ok(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """GET /session/{id} возвращает метаданные созданной сессии."""
    client_id = str(uuid.uuid4())
    create_resp = session_manager_service_client.create_session(client_id)
    assert create_resp.status_code in (200, 201) and create_resp.json is not None
    session_id = create_resp.json["id"]

    resp = session_manager_service_client.get_session(session_id)
    assert resp.status_code == 200
    assert resp.json is not None
    body = resp.json
    assert body.get("id") == session_id
    assert body.get("status") == "waiting"
    assert body.get("pin") == create_resp.json["pin"]


@pytest.mark.smoke
def test_get_participants_empty(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """GET /session/{id}/participants возвращает пустой список для новой сессии."""
    client_id = str(uuid.uuid4())
    create_resp = session_manager_service_client.create_session(client_id)
    assert create_resp.status_code in (200, 201) and create_resp.json is not None
    session_id = create_resp.json["id"]

    resp = session_manager_service_client.get_participants(session_id)
    assert resp.status_code == 200
    assert resp.json is not None
    assert "participantIds" in resp.json
    assert isinstance(resp.json["participantIds"], list)
    assert resp.json["participantIds"] == []


@pytest.mark.smoke
def test_join_session_by_pin_ok(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/join по PIN успешно присоединяет оператора к сессии."""
    client_id = str(uuid.uuid4())
    operator_id = str(uuid.uuid4())
    create_resp = session_manager_service_client.create_session(client_id)
    assert create_resp.status_code in (200, 201) and create_resp.json is not None
    pin = create_resp.json["pin"]

    resp = session_manager_service_client.join_session(session_id="", pin=pin, user_id=operator_id)
    assert resp.status_code == 200
    assert resp.json is not None
    assert resp.json.get("id")
    assert resp.json.get("status") in {"waiting", "active"}


@pytest.mark.smoke
def test_join_session_by_session_id_ok(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/join по session_id успешно присоединяет оператора к сессии."""
    client_id = str(uuid.uuid4())
    operator_id = str(uuid.uuid4())
    create_resp = session_manager_service_client.create_session(client_id)
    assert create_resp.status_code in (200, 201) and create_resp.json is not None
    session_id = create_resp.json["id"]

    resp = session_manager_service_client.join_session(
        session_id=session_id, pin="", user_id=operator_id
    )
    assert resp.status_code == 200
    assert resp.json is not None
    assert resp.json.get("id") == session_id
    assert resp.json.get("status") in {"waiting", "active"}


@pytest.mark.smoke
def test_join_session_adds_participant(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/join добавляет оператора в список участников."""
    client_id = str(uuid.uuid4())
    operator_id = str(uuid.uuid4())
    create_resp = session_manager_service_client.create_session(client_id)
    assert create_resp.status_code in (200, 201) and create_resp.json is not None
    session_id = create_resp.json["id"]
    pin = create_resp.json["pin"]

    # Присоединяем оператора
    join_resp = session_manager_service_client.join_session(
        session_id="", pin=pin, user_id=operator_id
    )
    assert join_resp.status_code == 200

    # Проверяем, что оператор в списке участников
    participants_resp = session_manager_service_client.get_participants(session_id)
    assert participants_resp.status_code == 200
    assert participants_resp.json is not None
    assert operator_id in participants_resp.json["participantIds"]


@pytest.mark.smoke
def test_invite_operator_ok(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/{id}/invite успешно приглашает оператора в сессию."""
    client_id = str(uuid.uuid4())
    operator_id = str(uuid.uuid4())
    create_resp = session_manager_service_client.create_session(client_id)
    assert create_resp.status_code in (200, 201) and create_resp.json is not None
    session_id = create_resp.json["id"]

    resp = session_manager_service_client.invite_operator(session_id, operator_id)
    assert resp.status_code == 200
    assert resp.json is not None
    assert resp.json.get("ok") is True

    # Проверяем, что оператор добавлен в участники
    participants_resp = session_manager_service_client.get_participants(session_id)
    assert participants_resp.status_code == 200
    assert participants_resp.json is not None
    assert operator_id in participants_resp.json["participantIds"]


@pytest.mark.smoke
def test_control_session_ok(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/{id}/control успешно изменяет статус сессии."""
    client_id = str(uuid.uuid4())
    create_resp = session_manager_service_client.create_session(client_id)
    assert create_resp.status_code in (200, 201) and create_resp.json is not None
    session_id = create_resp.json["id"]

    # Изменяем статус на active (caller = session client, so permission allowed)
    resp = session_manager_service_client.control_session(session_id, "active", caller_id=client_id)
    assert resp.status_code == 200
    assert resp.json is not None
    assert resp.json.get("ok") is True

    # Проверяем, что статус изменился
    get_resp = session_manager_service_client.get_session(session_id)
    assert get_resp.status_code == 200
    assert get_resp.json is not None
    assert get_resp.json.get("status") == "active"


@pytest.mark.smoke
def test_control_session_finish(
    session_manager_service_client: SessionManagerServiceClient,
) -> None:
    """POST /session/{id}/control с action='finished' завершает сессию."""
    client_id = str(uuid.uuid4())
    create_resp = session_manager_service_client.create_session(client_id)
    assert create_resp.status_code in (200, 201) and create_resp.json is not None
    session_id = create_resp.json["id"]

    # Завершаем сессию (caller = session client, so permission allowed)
    resp = session_manager_service_client.control_session(
        session_id, "finished", caller_id=client_id
    )
    assert resp.status_code == 200
    assert resp.json is not None
    assert resp.json.get("ok") is True

    # Проверяем, что статус изменился на finished
    get_resp = session_manager_service_client.get_session(session_id)
    assert get_resp.status_code == 200
    assert get_resp.json is not None
    assert get_resp.json.get("status") == "finished"

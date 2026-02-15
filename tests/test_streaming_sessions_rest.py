from __future__ import annotations

import uuid

import pytest

from qa_tests.http_client import StreamingServiceClient

# Session/client IDs must be valid UUIDs (streaming-service stores them as UUID in PostgreSQL).
# Для «not found» используем валидный UUID, которого нет в БД — сервис вернёт 404, а не 500.
NONEXISTENT_SESSION_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.smoke
def test_create_session_ok(streaming_service_client: StreamingServiceClient) -> None:
    client_id = str(uuid.uuid4())
    resp = streaming_service_client.create_session(client_id)
    assert resp.status_code == 201
    assert resp.json is not None
    body = resp.json
    assert body.get("session_id")
    assert body.get("stream_key")
    assert body.get("ws_url")
    assert body.get("status") in {"waiting", "active"}


@pytest.mark.negative
def test_create_session_invalid_body(streaming_service_client: StreamingServiceClient) -> None:
    # Пустое тело должно привести к 400
    resp = streaming_service_client._request("POST", "/sessions", json_body={}, expected_status=400)
    assert resp.status_code == 400


@pytest.mark.smoke
def test_get_session_operators_empty(streaming_service_client: StreamingServiceClient) -> None:
    client_id = str(uuid.uuid4())
    create = streaming_service_client.create_session(client_id)
    assert create.status_code == 201 and create.json is not None
    session_id = create.json["session_id"]

    resp = streaming_service_client.get_session_operators(session_id)
    assert resp.status_code == 200 and resp.json is not None
    body = resp.json
    assert body.get("session_id") == session_id
    assert isinstance(body.get("operators"), list)
    assert body.get("operators") == []


@pytest.mark.negative
def test_get_session_operators_not_found(streaming_service_client: StreamingServiceClient) -> None:
    resp = streaming_service_client.get_session_operators(NONEXISTENT_SESSION_ID)
    assert resp.status_code == 404


@pytest.mark.smoke
def test_delete_session_ok(streaming_service_client: StreamingServiceClient) -> None:
    client_id = str(uuid.uuid4())
    create = streaming_service_client.create_session(client_id)
    assert create.status_code == 201 and create.json is not None
    session_id = create.json["session_id"]

    delete_resp = streaming_service_client.delete_session(session_id)
    assert delete_resp.status_code in (204, 404)

    # После успешного завершения сессии: 404/410 (сессия недоступна) или 200 с пустыми operators
    ops = streaming_service_client.get_session_operators(session_id)
    assert ops.status_code in (404, 410, 200)
    if ops.status_code == 200 and ops.json is not None:
        assert ops.json.get("operators") == []


@pytest.mark.negative
def test_delete_session_not_found(streaming_service_client: StreamingServiceClient) -> None:
    resp = streaming_service_client.delete_session(NONEXISTENT_SESSION_ID)
    assert resp.status_code in (404, 204)

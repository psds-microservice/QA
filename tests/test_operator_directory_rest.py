"""REST API operator-directory-service: GET/POST/PUT /api/v1/operators."""

from __future__ import annotations

import uuid

import pytest

from qa_tests.http_client import OperatorDirectoryServiceClient

NONEXISTENT_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.smoke
def test_list_operators_empty(
    operator_directory_service_client: OperatorDirectoryServiceClient,
) -> None:
    """GET /api/v1/operators возвращает 200; operators — список или null (если pool недоступен)."""
    resp = operator_directory_service_client.list_operators()
    assert resp.status_code == 200
    assert resp.json is not None
    operators = resp.json.get("operators")
    assert operators is None or isinstance(operators, list)


@pytest.mark.smoke
def test_list_operators_with_params(
    operator_directory_service_client: OperatorDirectoryServiceClient,
) -> None:
    """GET /api/v1/operators с limit/offset возвращает 200."""
    resp = operator_directory_service_client.list_operators(limit=5, offset=0)
    assert resp.status_code == 200
    assert resp.json is not None
    assert resp.json.get("limit") == 5
    assert resp.json.get("offset") == 0


@pytest.mark.negative
def test_get_operator_not_found(
    operator_directory_service_client: OperatorDirectoryServiceClient,
) -> None:
    """GET /api/v1/operators/:id для несуществующего id — 404."""
    resp = operator_directory_service_client.get_operator(NONEXISTENT_ID)
    assert resp.status_code == 404


@pytest.mark.negative
def test_get_operator_invalid_id(
    operator_directory_service_client: OperatorDirectoryServiceClient,
) -> None:
    """GET /api/v1/operators/:id с невалидным UUID — 400."""
    resp = operator_directory_service_client.get_operator("not-a-uuid")
    assert resp.status_code == 400


@pytest.mark.smoke
def test_create_and_get_operator(
    operator_directory_service_client: OperatorDirectoryServiceClient,
) -> None:
    """POST /api/v1/operators создаёт запись, GET возвращает её."""
    user_id = str(uuid.uuid4())
    payload = {"user_id": user_id, "role": "operator", "display_name": "e2e-test"}
    create = operator_directory_service_client.create_operator(payload)
    assert create.status_code == 201
    assert create.json is not None
    # gRPC Gateway отдаёт JSON в camelCase (userId, displayName, role)
    op_id = create.json.get("userId") or create.json.get("user_id")
    assert op_id == user_id
    assert create.json.get("role") == "operator"

    # Get by id (service uses user_id as id in response)
    if op_id:
        get_resp = operator_directory_service_client.get_operator(op_id)
        assert get_resp.status_code == 200
        assert get_resp.json is not None
        assert (get_resp.json.get("userId") or get_resp.json.get("user_id")) == user_id


@pytest.mark.negative
def test_create_operator_invalid_body(
    operator_directory_service_client: OperatorDirectoryServiceClient,
) -> None:
    """POST /api/v1/operators без user_id — 400."""
    resp = operator_directory_service_client.create_operator({})
    assert resp.status_code == 400


@pytest.mark.negative
def test_create_operator_duplicate(
    operator_directory_service_client: OperatorDirectoryServiceClient,
) -> None:
    """POST /api/v1/operators с тем же user_id второй раз — 409."""
    user_id = str(uuid.uuid4())
    payload = {"user_id": user_id, "role": "operator"}
    first = operator_directory_service_client.create_operator(payload)
    assert first.status_code == 201
    second = operator_directory_service_client.create_operator(payload)
    assert second.status_code == 409


@pytest.mark.smoke
def test_update_operator(
    operator_directory_service_client: OperatorDirectoryServiceClient,
) -> None:
    """Создаём оператора, PUT обновляет display_name, GET возвращает обновлённые данные."""
    user_id = str(uuid.uuid4())
    create = operator_directory_service_client.create_operator(
        {"user_id": user_id, "role": "operator", "display_name": "before"}
    )
    assert create.status_code == 201 and create.json is not None
    op_id = create.json.get("userId") or create.json.get("user_id")
    assert op_id is not None

    update = operator_directory_service_client.update_operator(op_id, {"display_name": "after-e2e"})
    assert update.status_code == 200
    assert update.json is not None
    assert (update.json.get("displayName") or update.json.get("display_name")) == "after-e2e"

    get_resp = operator_directory_service_client.get_operator(op_id)
    assert get_resp.status_code == 200
    assert get_resp.json is not None
    assert (get_resp.json.get("displayName") or get_resp.json.get("display_name")) == "after-e2e"


@pytest.mark.negative
def test_update_operator_not_found(
    operator_directory_service_client: OperatorDirectoryServiceClient,
) -> None:
    """PUT /api/v1/operators/:id для несуществующего id — 404."""
    resp = operator_directory_service_client.update_operator(NONEXISTENT_ID, {"display_name": "x"})
    assert resp.status_code == 404

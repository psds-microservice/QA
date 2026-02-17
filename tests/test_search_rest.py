"""REST API search-service: GET /search, POST /search/index/*."""

from __future__ import annotations

import uuid

import pytest

from qa_tests.http_client import SearchServiceClient


@pytest.mark.smoke
def test_search_empty_query(search_service_client: SearchServiceClient) -> None:
    """GET /search с пустым запросом возвращает 200."""
    resp = search_service_client.search("")
    assert resp.status_code == 200
    assert resp.json is not None


@pytest.mark.smoke
def test_search_with_query(search_service_client: SearchServiceClient) -> None:
    """GET /search?q=test возвращает 200."""
    resp = search_service_client.search("test")
    assert resp.status_code == 200
    assert resp.json is not None


@pytest.mark.smoke
def test_search_with_type_filter(search_service_client: SearchServiceClient) -> None:
    """GET /search?q=test&type=tickets возвращает 200."""
    resp = search_service_client.search("test", type_filter="tickets")
    assert resp.status_code == 200
    assert resp.json is not None


@pytest.mark.smoke
def test_search_with_limit(search_service_client: SearchServiceClient) -> None:
    """GET /search?q=test&limit=10 возвращает 200."""
    resp = search_service_client.search("test", limit=10)
    assert resp.status_code == 200
    assert resp.json is not None


@pytest.mark.smoke
def test_index_ticket_ok(search_service_client: SearchServiceClient) -> None:
    """POST /search/index/ticket с валидным payload — 200."""
    payload = {
        "ticket_id": 12345,
        "session_id": str(uuid.uuid4()),
        "client_id": str(uuid.uuid4()),
        "operator_id": str(uuid.uuid4()),
        "subject": "Test ticket",
        "notes": "Test notes",
        "status": "open",
    }
    resp = search_service_client.index_ticket(payload)
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("ok") is True


@pytest.mark.smoke
def test_index_session_ok(search_service_client: SearchServiceClient) -> None:
    """POST /search/index/session с валидным payload — 200."""
    payload = {
        "session_id": str(uuid.uuid4()),
        "client_id": str(uuid.uuid4()),
        "pin": "1234",
        "status": "active",
    }
    resp = search_service_client.index_session(payload)
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("ok") is True


@pytest.mark.smoke
def test_index_operator_ok(search_service_client: SearchServiceClient) -> None:
    """POST /search/index/operator с валидным payload — 200."""
    payload = {
        "user_id": str(uuid.uuid4()),
        "display_name": "Test Operator",
        "region": "ru-msk",
        "role": "operator",
    }
    resp = search_service_client.index_operator(payload)
    assert resp.status_code == 200
    if resp.json:
        assert resp.json.get("ok") is True


@pytest.mark.negative
def test_index_ticket_invalid_json(search_service_client: SearchServiceClient) -> None:
    """POST /search/index/ticket с невалидным JSON — 400."""
    # Отправляем невалидный JSON (не объект)
    import requests

    url = f"{search_service_client.base_url.rstrip('/')}/search/index/ticket"
    resp = requests.post(url, data="not json", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400


@pytest.mark.negative
def test_index_session_invalid_json(search_service_client: SearchServiceClient) -> None:
    """POST /search/index/session с невалидным JSON — 400."""
    import requests

    url = f"{search_service_client.base_url.rstrip('/')}/search/index/session"
    resp = requests.post(url, data="not json", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400


@pytest.mark.negative
def test_index_operator_invalid_json(search_service_client: SearchServiceClient) -> None:
    """POST /search/index/operator с невалидным JSON — 400."""
    import requests

    url = f"{search_service_client.base_url.rstrip('/')}/search/index/operator"
    resp = requests.post(url, data="not json", headers={"Content-Type": "application/json"})
    assert resp.status_code == 400


@pytest.mark.negative
def test_index_ticket_empty_body(search_service_client: SearchServiceClient) -> None:
    """POST /search/index/ticket с пустым объектом {} — 400."""
    # Пустой объект {} — валидный JSON, но Elasticsearch возвращает ошибку валидации
    resp = search_service_client.index_ticket({})
    assert resp.status_code == 400


@pytest.mark.negative
def test_index_session_empty_body(search_service_client: SearchServiceClient) -> None:
    """POST /search/index/session с пустым объектом {} — 400."""
    resp = search_service_client.index_session({})
    assert resp.status_code == 400


@pytest.mark.negative
def test_index_operator_empty_body(search_service_client: SearchServiceClient) -> None:
    """POST /search/index/operator с пустым объектом {} — 400."""
    resp = search_service_client.index_operator({})
    assert resp.status_code == 400

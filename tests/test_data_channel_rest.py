"""REST API data-channel-service: GET /data/:session_id/history, POST /data/file."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from qa_tests.http_client import DataChannelServiceClient


@pytest.mark.smoke
def test_get_history_empty(
    data_channel_service_client: DataChannelServiceClient,
) -> None:
    """GET /data/:session_id/history возвращает 200 с пустым списком."""
    session_id = str(uuid.uuid4())
    resp = data_channel_service_client.get_history(session_id)
    assert resp.status_code == 200
    assert resp.json is not None
    # gRPC Gateway возвращает объект { "messages": [...] }
    assert "messages" in resp.json
    assert isinstance(resp.json["messages"], list)


@pytest.mark.smoke
def test_get_history_with_limit(
    data_channel_service_client: DataChannelServiceClient,
) -> None:
    """GET /data/:session_id/history?limit=10 возвращает 200."""
    session_id = str(uuid.uuid4())
    resp = data_channel_service_client.get_history(session_id, limit=10)
    assert resp.status_code == 200
    assert resp.json is not None
    assert "messages" in resp.json
    assert isinstance(resp.json["messages"], list)


@pytest.mark.negative
def test_get_history_invalid_session_id(
    data_channel_service_client: DataChannelServiceClient,
) -> None:
    """GET /data/:session_id/history с невалидным UUID — 400."""
    resp = data_channel_service_client.get_history("not-a-uuid")
    assert resp.status_code == 400


@pytest.mark.smoke
def test_upload_file_ok(
    data_channel_service_client: DataChannelServiceClient, tmp_path: Path
) -> None:
    """POST /data/file с валидным файлом — 200."""
    session_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())

    # Создаём временный файл для загрузки
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content", encoding="utf-8")

    resp = data_channel_service_client.upload_file(
        session_id=session_id, user_id=user_id, file_path=str(test_file)
    )
    assert resp.status_code == 200
    assert resp.json is not None
    assert "id" in resp.json
    assert "filename" in resp.json
    assert "url" in resp.json


@pytest.mark.negative
def test_upload_file_invalid_session_id(
    data_channel_service_client: DataChannelServiceClient, tmp_path: Path
) -> None:
    """POST /data/file с невалидным session_id — 400."""
    user_id = str(uuid.uuid4())
    test_file = tmp_path / "test.txt"
    test_file.write_text("test", encoding="utf-8")

    resp = data_channel_service_client.upload_file(
        session_id="not-a-uuid", user_id=user_id, file_path=str(test_file)
    )
    assert resp.status_code == 400


@pytest.mark.negative
def test_upload_file_invalid_user_id(
    data_channel_service_client: DataChannelServiceClient, tmp_path: Path
) -> None:
    """POST /data/file с невалидным user_id — 400."""
    session_id = str(uuid.uuid4())
    test_file = tmp_path / "test.txt"
    test_file.write_text("test", encoding="utf-8")

    resp = data_channel_service_client.upload_file(
        session_id=session_id, user_id="not-a-uuid", file_path=str(test_file)
    )
    assert resp.status_code == 400

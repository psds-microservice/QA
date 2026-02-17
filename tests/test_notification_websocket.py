"""WebSocket API notification-service: GET /ws/notify/:user_id."""

from __future__ import annotations

import asyncio
import uuid

import pytest

from qa_tests.config import get_settings
from qa_tests.http_client import NotificationServiceClient
from qa_tests.ws_client import WebSocketClient


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_notification_websocket_connect_ok(
    notification_service_client: NotificationServiceClient,
) -> None:
    """GET /ws/notify/:user_id — успешное подключение по валидному user_id."""
    settings = get_settings()
    ws_base = settings.notification_ws.base_url.rstrip("/")

    user_id = str(uuid.uuid4())
    ws_url = f"{ws_base}/ws/notify/{user_id}"

    ws = WebSocketClient(url=ws_url)
    try:
        await ws.connect()
        # Подключение успешно, можно закрывать
        assert ws._conn is not None
    finally:
        await ws.close()


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_notification_websocket_receive_broadcast(
    notification_service_client: NotificationServiceClient,
) -> None:
    """WebSocket получает сообщение после подписки на сессию и POST /notify/session/:id."""
    settings = get_settings()
    ws_base = settings.notification_ws.base_url.rstrip("/")

    user_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    ws_url = f"{ws_base}/ws/notify/{user_id}"

    ws = WebSocketClient(url=ws_url)
    try:
        await ws.connect()

        # Подписываемся на сессию через WebSocket (отправляем JSON)
        subscribe_msg = {"subscribe_session": session_id}
        await ws.send_json(subscribe_msg)

        # Небольшая задержка для обработки подписки
        await asyncio.sleep(0.5)

        # Отправляем уведомление через REST API
        payload = {"event": "session.started", "payload": {"session_id": session_id}}
        notify_resp = notification_service_client.notify_session(session_id, payload)
        assert notify_resp.status_code == 200

        # Ждём сообщение через WebSocket
        msg = await asyncio.wait_for(ws.receive(), timeout=3.0)
        assert msg.raw is not None
        if msg.json:
            assert "event" in msg.json
            assert msg.json["event"] == "session.started"

    finally:
        await ws.close()


@pytest.mark.asyncio
@pytest.mark.negative
async def test_notification_websocket_invalid_user_id() -> None:
    """GET /ws/notify/:user_id с невалидным UUID — 400."""
    settings = get_settings()

    # WebSocket при 400 не подключается; проверяем HTTP-ответ
    import requests

    http_base = settings.notification_service.base_url.rstrip("/")
    resp = requests.get(f"{http_base}/ws/notify/not-a-uuid")
    assert resp.status_code == 400


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_notification_websocket_with_query_params(
    notification_service_client: NotificationServiceClient,
) -> None:
    """GET /ws/notify/:user_id?region=ru-msk&roles=operator — подключение с query params."""
    settings = get_settings()
    ws_base = settings.notification_ws.base_url.rstrip("/")

    user_id = str(uuid.uuid4())
    ws_url = f"{ws_base}/ws/notify/{user_id}?region=ru-msk&roles=operator,premium"

    ws = WebSocketClient(url=ws_url)
    try:
        await ws.connect()
        assert ws._conn is not None
    finally:
        await ws.close()

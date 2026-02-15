from __future__ import annotations

import asyncio
import uuid

import pytest

from qa_tests.config import get_settings
from qa_tests.http_client import StreamingServiceClient
from qa_tests.ws_client import WebSocketClient

# Valid UUID that does not exist in DB — service returns 404 instead of 500 on invalid UUID.
NONEXISTENT_SESSION_ID = "00000000-0000-0000-0000-000000000001"


@pytest.mark.asyncio
@pytest.mark.smoke
async def test_stream_broadcast_from_client_to_operator(
    streaming_service_client: StreamingServiceClient,
) -> None:
    settings = get_settings()
    ws_base = settings.streaming_ws.base_url.rstrip("/")

    client_id = str(uuid.uuid4())
    # Создаём сессию
    create = streaming_service_client.create_session(client_id)
    assert create.status_code == 201 and create.json is not None
    session_id = create.json["session_id"]

    # WebSocket URL: /ws/stream/:session_id/:user_id
    client_ws_url = f"{ws_base}/ws/stream/{session_id}/{client_id}"
    operator_id = str(uuid.uuid4())
    operator_ws_url = f"{ws_base}/ws/stream/{session_id}/{operator_id}"

    client_ws = WebSocketClient(url=client_ws_url)
    operator_ws = WebSocketClient(url=operator_ws_url)

    try:
        await asyncio.gather(client_ws.connect(), operator_ws.connect())

        # Клиент отправляет несколько сообщений, оператор должен их получить
        payloads = [f"frame-{i}" for i in range(3)]

        async def sender() -> None:
            for p in payloads:
                await client_ws._conn.send(p)

        received: list[str] = []

        async def receiver() -> None:
            while len(received) < len(payloads):
                msg = await operator_ws.receive()
                received.append(msg.raw)

        await asyncio.wait_for(asyncio.gather(sender(), receiver()), timeout=10.0)

        assert received == payloads

    finally:
        await asyncio.gather(
            client_ws.close(),
            operator_ws.close(),
            return_exceptions=True,
        )


@pytest.mark.asyncio
@pytest.mark.negative
async def test_ws_session_not_found(streaming_service_client: StreamingServiceClient) -> None:
    settings = get_settings()
    session_id = NONEXISTENT_SESSION_ID
    user_id = str(uuid.uuid4())

    # Подключение к несуществующей сессии — 404; проверяем HTTP-ответ (ws при 404 бросает).
    import requests

    http_base = settings.streaming_service.base_url.rstrip("/")
    resp = requests.get(f"{http_base}/ws/stream/{session_id}/{user_id}")
    assert resp.status_code == 404

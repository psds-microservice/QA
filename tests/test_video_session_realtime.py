from __future__ import annotations

import asyncio
import json
import time
from typing import Dict

import allure
import pytest

from qa_tests import data_factory
from qa_tests.allure_utils import allure_step, attach_json, link_jira, mark_feature, mark_severity, mark_story
from qa_tests.http_client import ApiGatewayClient
from qa_tests.metrics import measure_test_case
from qa_tests.models import AuthRequest, CreateSessionRequest, CreateSessionResponse
from qa_tests.ws_client import WebSocketClient


@pytest.mark.websocket
@pytest.mark.asyncio
@allure.tag("video", "websocket")
async def test_video_session_message_exchange(api_gateway_client: ApiGatewayClient) -> None:
    """Создание видеосессии, подключение оператора и обмен сообщениями по WebSocket."""
    mark_feature("Video Consultation")
    mark_story("Создание сессии и real-time чат")
    mark_severity("critical")
    link_jira("PSDS-201")

    async with measure_test_case("test_video_session_message_exchange"):  # type: ignore[misc]
        # Arrange: пользователь и оператор
        with allure_step("Подготовка пользователя и получение токена"):
            user_payload = data_factory.build_user_registration()
            reg_resp = api_gateway_client.register_user(user_payload)
            assert reg_resp.status_code == 201

            auth = api_gateway_client.authenticate(
                AuthRequest(email=user_payload["email"], password=user_payload["password"]).model_dump()
            )
            assert auth.status_code == 200 and auth.json is not None
            user_token = auth.json["access_token"]

        with allure_step("Создание видеосессии пользователем"):
            session_req = CreateSessionRequest(user_id=reg_resp.json["id"], reason="e2e test").model_dump()  # type: ignore[index]
            session_resp = api_gateway_client.create_video_session(user_token, session_req)
            assert session_resp.status_code == 201 and session_resp.json is not None
            attach_json("create_session_response", json.dumps(session_resp.json, ensure_ascii=False, indent=2))
            session = CreateSessionResponse.model_validate(session_resp.json)

        with allure_step("Подключение оператора к сессии"):
            operator_id = "operator-e2e-1"
            join_resp = api_gateway_client.join_video_session(user_token, session.session_id, operator_id)
            assert join_resp.status_code == 200

        with allure_step("Установление WebSocket-соединения пользователем и оператором"):
            user_ws = WebSocketClient(url=session.ws_url, token=user_token)
            operator_ws = WebSocketClient(url=session.ws_url, token=user_token)  # в реальности свой токен

            await asyncio.gather(user_ws.connect(), operator_ws.connect())

        try:
            with allure_step("Обмен сообщениями в режиме реального времени"):
                message_payload: Dict[str, object] = {
                    "type": "chat_message",
                    "content": "Hello from user",
                    "sender": "user",
                    "sent_at": time.time(),
                }
                await user_ws.send_json(message_payload)
                received = await operator_ws.receive()
                attach_json("received_message", received.raw)

                assert received.json is not None
                assert received.json.get("content") == message_payload["content"]
        finally:
            await asyncio.gather(user_ws.close(), operator_ws.close())


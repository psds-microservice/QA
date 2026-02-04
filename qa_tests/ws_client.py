from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Optional

import websockets
from websockets.client import WebSocketClientProtocol

from .logging_utils import get_logger
from .metrics import measure_request
from .retry import RetryConfig, retry_on_exceptions


logger = get_logger(__name__)


@dataclass
class WebSocketMessage:
    raw: str
    json: Optional[Dict[str, Any]]


@dataclass
class WebSocketClient:
    url: str
    token: Optional[str] = None

    _conn: Optional[WebSocketClientProtocol] = None

    @retry_on_exceptions(exceptions=[OSError, websockets.WebSocketException], config=RetryConfig())
    async def connect(self) -> WebSocketClientProtocol:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        async def status_getter() -> str:
            return "connected" if self._conn and self._conn.open else "closed"

        async with measure_request("ws", "CONNECT", lambda: asyncio.get_event_loop().run_until_complete(status_getter())):  # type: ignore[arg-type]
            self._conn = await websockets.connect(self.url, extra_headers=headers, ping_interval=20)

        logger.info("WebSocket connected", extra={"url": self.url})
        return self._conn

    async def send_json(self, payload: Dict[str, Any]) -> None:
        if not self._conn:
            await self.connect()
        assert self._conn is not None
        message = json.dumps(payload)
        await self._conn.send(message)
        logger.info("WebSocket send", extra={"payload": payload})

    async def receive(self) -> WebSocketMessage:
        if not self._conn:
            await self.connect()
        assert self._conn is not None
        raw = await self._conn.recv()
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = None
        logger.info("WebSocket receive", extra={"raw": raw})
        return WebSocketMessage(raw=raw, json=payload)

    async def __aiter__(self) -> AsyncIterator[WebSocketMessage]:
        while True:
            yield await self.receive()

    async def close(self) -> None:
        if self._conn and self._conn.open:
            await self._conn.close()
            logger.info("WebSocket closed", extra={"url": self.url})


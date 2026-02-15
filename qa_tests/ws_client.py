from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, Optional

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import WebSocketException

from .logging_utils import get_logger
from .metrics import measure_request_async
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

    _conn: Optional[ClientConnection] = None

    @retry_on_exceptions(exceptions=[OSError, WebSocketException], config=RetryConfig())
    async def connect(self) -> ClientConnection:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        # ws16: additional_headers; extra_headers would be passed to event loop (TypeError)
        connect_kwargs: Dict[str, Any] = {"ping_interval": 20}
        if headers:
            connect_kwargs["additional_headers"] = headers
        async with measure_request_async(
            "ws", "CONNECT", lambda: "connected" if self._conn is not None else "closed"
        ):
            self._conn = await connect(self.url, **connect_kwargs)

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
        # websockets 16+ recv() may return bytes; normalize to str for WebSocketMessage.raw
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
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
        if self._conn:
            await self._conn.close()
            logger.info("WebSocket closed", extra={"url": self.url})

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """Форматтер, логирующий сообщения в JSON-формате.

    Подходит для сбора логов в централизованные системы и удобного анализа.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key.startswith("_"):
                continue
            if key in payload:
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except TypeError:
                payload[key] = repr(value)

        return json.dumps(payload, ensure_ascii=False)


def configure_root_logger(level: int = logging.INFO) -> None:
    """Конфигурирует корневой логгер в JSON-формате.

    Вызывать один раз при старте тестового раннера (например, в conftest.py).
    """
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    root.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Возвращает именованный логгер."""
    return logging.getLogger(name)

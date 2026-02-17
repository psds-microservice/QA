from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv


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
    Если задана переменная окружения TEST_LOG_FILE, логи также сохраняются в файл.
    """
    # Загружаем .env файл, если он есть (для чтения TEST_LOG_FILE)
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)

    handlers: list[logging.Handler] = []

    # Всегда выводим в stdout
    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.setFormatter(JsonFormatter())
    handlers.append(stdout_handler)

    # Если задан файл — добавляем FileHandler
    log_file = os.getenv("TEST_LOG_FILE")
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(JsonFormatter())
            handlers.append(file_handler)
            # Логируем в stderr, что файл создан (до настройки root logger)
            print(f"[LOG] Logging to file: {log_path.resolve()}", file=sys.stderr)
        except Exception as e:
            # Если не удалось создать файл — продолжаем без него, но предупреждаем
            print(f"[WARN] Failed to create log file '{log_file}': {e}", file=sys.stderr)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()
    for handler in handlers:
        root.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Возвращает именованный логгер."""
    return logging.getLogger(name)

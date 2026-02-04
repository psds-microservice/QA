"""Конфигурация тестов: проверка доступности сервисов без автоматического Docker."""

from __future__ import annotations

import time

import pytest
import requests


@pytest.fixture(scope="session", autouse=True)
def wait_for_services(settings) -> None:  # type: ignore[no-untyped-def]
    """
    Проверяет, что API Gateway доступен по настроенному URL (сервисы уже запущены).
    Не поднимает Docker — для локального прогона запустите api-gateway/user-service вручную
    или используйте: make test-with-docker.
    """
    api_url = f"{settings.api_gateway.base_url.rstrip('/')}/health"
    timeout_sec = 30.0
    pause_sec = 2.0
    deadline = time.monotonic() + timeout_sec

    while time.monotonic() < deadline:
        try:
            resp = requests.get(api_url, timeout=3)
            if resp.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(pause_sec)

    pytest.exit(
        f"API Gateway недоступен по адресу {api_url}. "
        "Запустите api-gateway и user-service вручную или выполните: make test-with-docker",
        returncode=2,
    )


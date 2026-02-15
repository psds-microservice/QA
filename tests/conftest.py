"""Конфигурация тестов: проверка доступности сервисов без автоматического Docker."""

from __future__ import annotations

import time

import pytest
import requests


def pytest_collection_finish(session: pytest.Session) -> None:
    """
    Если запущены только тесты API Gateway — сразу проверяем доступность и тип сервиса.
    Два разных исхода: «сервис недоступен» vs «по этому URL не API Gateway».
    """
    gateway_markers = ("test_api_gateway", "test_rate_limiting")
    items = getattr(session, "items", [])
    if not items:
        return
    only_gateway = all(
        any(m in (getattr(item, "nodeid", "") or "") for m in gateway_markers) for item in items
    )
    if not only_gateway:
        return
    from qa_tests.config import get_settings

    settings = get_settings()
    base = settings.api_gateway.base_url.rstrip("/")
    health_url = f"{base}/health"
    status_url = f"{base}/api/v1/status"

    # 1) Есть ли вообще ответ по этому адресу?
    try:
        r_health = requests.get(health_url, timeout=5)
    except requests.RequestException as e:
        pytest.exit(
            f"Сервис недоступен: по адресу {base} не удалось подключиться ({e!r}). "
            "Запустите API Gateway и укажите в .env API_GATEWAY_BASE_URL (например :8081).",
            returncode=3,
        )
    if r_health.status_code != 200:
        pytest.exit(
            f"Сервис по адресу {base} ответил на GET /health кодом {r_health.status_code}. "
            "Для тестов API Gateway нужен запущенный gateway с рабочим /health.",
            returncode=3,
        )

    # 2) Это именно API Gateway?
    # 2a) В GET /health тело содержит "service": "api-gateway" (psds/api-gateway)
    try:
        health_json = r_health.json()
        if health_json.get("service") == "api-gateway":
            return
        if (
            isinstance(health_json.get("service"), str)
            and "gateway" in health_json.get("service", "").lower()
        ):
            return
    except Exception:
        pass

    # 2b) GET /api/v1/status или GET /api/v1/test/endpoints (есть только в psds/api-gateway)
    for check_url in (status_url, f"{base}/api/v1/test/endpoints"):
        try:
            r = requests.get(check_url, timeout=5)
            if r.status_code == 200:
                return
        except Exception:
            pass

    # 2c) OpenAPI по /openapi.json с путями video или clients
    openapi_urls = [
        f"{base}/openapi.json",
        f"{base}/swagger/openapi.json",
        f"{base}/swagger/doc.json",
    ]
    gateway_path_examples = [
        "/api/v1/status",
        "/api/v1/video/start",
        "/api/v1/video/frame",
        "/api/v1/video/stop",
        "/api/v1/clients/active",
    ]
    for spec_url in openapi_urls:
        try:
            r_spec = requests.get(spec_url, timeout=5)
            if r_spec.status_code != 200:
                continue
            spec = r_spec.json()
            paths = spec.get("paths") or {}
            if any(p in paths for p in gateway_path_examples):
                return
        except Exception:
            continue

    pytest.exit(
        f"По адресу {base} отвечает сервис (health 200), но это не API Gateway: "
        f"нет GET /api/v1/status и в OpenAPI нет путей video/status. "
        "Укажите в .env API_GATEWAY_BASE_URL на URL именно API Gateway.",
        returncode=4,
    )


def _only_streaming_tests_collected(session: pytest.Session) -> bool:
    """True, если в сессии собраны только тесты из test_streaming_*.py."""
    if not session.items:
        return False
    return all("test_streaming" in (getattr(item, "nodeid", "") or "") for item in session.items)


def _only_operator_directory_tests_collected(session: pytest.Session) -> bool:
    """True, если в сессии только тесты из test_operator_directory_*.py."""
    if not session.items:
        return False
    return all(
        "test_operator_directory" in (getattr(item, "nodeid", "") or "") for item in session.items
    )


@pytest.fixture(scope="session", autouse=True)
def wait_for_services(settings, request: pytest.FixtureRequest) -> None:
    """
    Проверяет доступность сервисов по настроенным URL (сервисы уже запущены).
    Если только тесты Streaming / Operator Directory — проверяется только этот сервис;
    иначе — API Gateway.
    Не поднимает Docker — для локального прогона запустите нужные сервисы вручную
    или используйте: make test-with-docker.
    """
    session = request.session
    if _only_operator_directory_tests_collected(session):
        base_url = settings.operator_directory_service.base_url.rstrip("/")
        service_name = "Operator Directory Service"
        hint = "Запустите operator-directory-service вручную или: make test-with-docker"
    elif _only_streaming_tests_collected(session):
        base_url = settings.streaming_service.base_url.rstrip("/")
        service_name = "Streaming Service"
        hint = "Запустите streaming-service вручную или выполните: make test-with-docker"
    else:
        base_url = settings.api_gateway.base_url.rstrip("/")
        service_name = "API Gateway"
        hint = "Запустите api-gateway и user-service вручную или выполните: make test-with-docker"

    health_url = f"{base_url}/health"
    timeout_sec = 30.0
    pause_sec = 2.0
    deadline = time.monotonic() + timeout_sec

    while time.monotonic() < deadline:
        try:
            resp = requests.get(health_url, timeout=3)
            if resp.status_code == 200:
                return
        except Exception:
            pass
        time.sleep(pause_sec)

    pytest.exit(
        f"{service_name} недоступен по адресу {health_url}. {hint}",
        returncode=2,
    )

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterator

import allure
import pytest

from .config import get_settings
from .http_client import (
    ApiGatewayClient,
    NotificationServiceClient,
    OperatorDirectoryServiceClient,
    OperatorPoolServiceClient,
    SearchServiceClient,
    StreamingServiceClient,
    TicketServiceClient,
    UserServiceClient,
)
from .logging_utils import configure_root_logger


@pytest.fixture(scope="session", autouse=True)
def configure_logging() -> None:
    """Глобальная настройка логирования для всех тестов."""
    configure_root_logger()


@pytest.fixture(scope="session")
def settings():
    """Глобальные настройки фреймворка."""
    return get_settings()


@pytest.fixture(scope="session")
def api_gateway_client(settings) -> ApiGatewayClient:
    """Client Object для API Gateway / User Service (пути из settings.api_paths)."""
    return ApiGatewayClient(
        base_url=settings.api_gateway.base_url,
        api_paths=settings.api_paths,
    )


@pytest.fixture(scope="session")
def user_service_client(settings) -> UserServiceClient:
    """Client Object для user-service."""
    return UserServiceClient(base_url=settings.user_service.base_url)


@pytest.fixture(scope="session")
def streaming_service_client(settings) -> StreamingServiceClient:
    """Client Object для streaming-service (REST)."""
    return StreamingServiceClient(base_url=settings.streaming_service.base_url)


@pytest.fixture(scope="session")
def operator_directory_service_client(settings) -> OperatorDirectoryServiceClient:
    """Client для operator-directory-service (health, /api/v1/operators CRUD)."""
    return OperatorDirectoryServiceClient(base_url=settings.operator_directory_service.base_url)


@pytest.fixture(scope="session")
def operator_pool_service_client(settings) -> OperatorPoolServiceClient:
    """Client для operator-pool-service (health, /operator/status, next, stats, list)."""
    return OperatorPoolServiceClient(base_url=settings.operator_pool_service.base_url)


@pytest.fixture(scope="session")
def notification_service_client(settings) -> NotificationServiceClient:
    """Client для notification-service (health, /notify/session/:id)."""
    return NotificationServiceClient(base_url=settings.notification_service.base_url)


@pytest.fixture(scope="session")
def search_service_client(settings) -> SearchServiceClient:
    """Client для search-service (health, /search, /search/index/*)."""
    return SearchServiceClient(base_url=settings.search_service.base_url)


@pytest.fixture(scope="session")
def ticket_service_client(settings) -> TicketServiceClient:
    """Client для ticket-service (health, /api/v1/tickets CRUD)."""
    return TicketServiceClient(base_url=settings.ticket_service.base_url)


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Отдельный event loop для pytest-asyncio."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def video_artifacts_tmpdir(tmp_path: Path) -> Path:
    """Каталог для сохранения скриншотов/видео при падении."""
    path = tmp_path / "video_artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    # Позволяет узнавать статус теста внутри фикстур
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(autouse=True)
def attach_artifacts_on_failure(request, video_artifacts_tmpdir: Path) -> Iterator[None]:
    """Автоматическое прикрепление артефактов при падении теста.

    Здесь можно интегрировать:
    - скриншоты UI-клиента;
    - один кадр из записанного видео WebRTC;
    - дампы сети/логов.
    """
    yield
    failed = False
    for phase in ("setup", "call", "teardown"):
        rep = getattr(request.node, f"rep_{phase}", None)
        if rep and rep.failed:
            failed = True
            break

    if failed:
        # пример: прикрепляем placeholder-файл, если он есть
        placeholder = video_artifacts_tmpdir / "failure-placeholder.txt"
        if placeholder.exists():
            with placeholder.open("r", encoding="utf-8") as f:
                allure.attach(
                    f.read(),
                    name="failure-placeholder",
                    attachment_type=allure.attachment_type.TEXT,
                )

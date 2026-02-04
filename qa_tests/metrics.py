from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Callable, Dict, Iterator

from prometheus_client import Counter, Histogram


_REQUEST_LATENCY = Histogram(
    "psds_test_request_latency_seconds",
    "Время выполнения HTTP/WebSocket запросов в тестах",
    ["service", "operation", "status"],
)

_TEST_DURATION = Histogram(
    "psds_test_case_duration_seconds",
    "Время выполнения тест-кейсов",
    ["test_name", "status"],
)

_TEST_FAILURES = Counter(
    "psds_test_failures_total",
    "Количество упавших тестов",
    ["test_name"],
)


@contextmanager
def measure_request(service: str, operation: str, status_getter: Callable[[], str]) -> Iterator[None]:
    """Контекстный менеджер для измерения времени HTTP/WebSocket запросов."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        status = status_getter()
        _REQUEST_LATENCY.labels(service=service, operation=operation, status=status).observe(elapsed)


@contextmanager
def measure_test_case(test_name: str) -> Iterator[Dict[str, float]]:
    """Измеряет длительность тест-кейса и обновляет метрики."""
    start = time.perf_counter()
    status = "passed"
    try:
        yield {"start": start}
    except Exception:
        status = "failed"
        _TEST_FAILURES.labels(test_name=test_name).inc()
        raise
    finally:
        elapsed = time.perf_counter() - start
        _TEST_DURATION.labels(test_name=test_name, status=status).observe(elapsed)


@dataclass
class TimingInfo:
    duration_seconds: float


def time_function(func: Callable[..., object]) -> Callable[..., object]:
    """Декоратор для измерения времени выполнения вспомогательных функций."""

    def wrapper(*args: object, **kwargs: object) -> object:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.perf_counter() - start
            # Здесь можно логировать или отправлять метрики при необходимости
            _ = TimingInfo(duration_seconds=elapsed)

    return wrapper


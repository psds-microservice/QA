from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterable, Tuple, Type, TypeVar

from .logging_utils import get_logger


T = TypeVar("T")

logger = get_logger(__name__)


@dataclass(frozen=True)
class RetryConfig:
    attempts: int = 3
    delay_seconds: float = 1.0
    backoff_factor: float = 2.0


def retry_on_exceptions(
    exceptions: Iterable[Type[BaseException]],
    config: RetryConfig | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Декоратор для повторного выполнения функций при временных ошибках."""
    cfg = config or RetryConfig()
    exceptions_tuple: Tuple[Type[BaseException], ...] = tuple(exceptions)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: object, **kwargs: object) -> T:
            delay = cfg.delay_seconds
            last_exc: BaseException | None = None

            for attempt in range(1, cfg.attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions_tuple as exc:  # type: ignore[misc]
                    last_exc = exc
                    logger.warning(
                        "Retryable error in %s: %s (attempt %s/%s)",
                        func.__name__,
                        exc,
                        attempt,
                        cfg.attempts,
                    )
                    if attempt == cfg.attempts:
                        break
                    time.sleep(delay)
                    delay *= cfg.backoff_factor

            assert last_exc is not None
            raise last_exc

        return wrapper

    return decorator


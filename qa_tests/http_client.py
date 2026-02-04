from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Type, TypeVar, Union

import requests
from requests import Response

from .config import ApiPaths
from .logging_utils import get_logger
from .metrics import measure_request
from .retry import RetryConfig, retry_on_exceptions


T = TypeVar("T")

logger = get_logger(__name__)


@dataclass
class ApiResponse:
    status_code: int
    json: Dict[str, Any] | None
    raw: Response


@dataclass
class BaseApiClient:
    base_url: str
    default_headers: Optional[Dict[str, str]] = None

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"

    @retry_on_exceptions(exceptions=[requests.RequestException], config=RetryConfig())
    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        expected_status: Optional[Union[int, Sequence[int]]] = None,
    ) -> ApiResponse:
        url = self._url(path)
        merged_headers = {**(self.default_headers or {}), **(headers or {})}

        with measure_request("api", f"{method.upper()} {path}", lambda: str(resp.status_code)):
            resp = requests.request(method, url, json=json_body, headers=merged_headers, timeout=10)

        if expected_status is not None:
            allowed = (expected_status,) if isinstance(expected_status, int) else tuple(expected_status)
            if resp.status_code not in allowed:
                logger.error(
                    "Unexpected status code",
                    extra={
                        "url": url,
                        "method": method,
                        "expected_status": expected_status,
                        "actual_status": resp.status_code,
                        "body": resp.text,
                    },
                )

        try:
            payload = resp.json()
        except ValueError:
            payload = None

        return ApiResponse(status_code=resp.status_code, json=payload, raw=resp)


class ApiGatewayClient(BaseApiClient):
    """Client Object для API Gateway. Пути эндпоинтов задаются через api_paths (из конфига)."""

    def __init__(
        self,
        base_url: str,
        default_headers: Optional[Dict[str, str]] = None,
        api_paths: Optional[ApiPaths] = None,
    ) -> None:
        super().__init__(base_url=base_url, default_headers=default_headers)
        self._paths = api_paths

    def _p(self, key: str, **kwargs: str) -> str:
        if self._paths is None:
            raise ValueError("ApiGatewayClient requires api_paths")
        path = getattr(self._paths, key)
        return path.format(**kwargs) if kwargs else path

    def register_user(self, payload: Dict[str, Any]) -> ApiResponse:
        # User Service возвращает 200, классический REST — 201
        return self._request(
            "POST", self._p("users_register"), json_body=payload, expected_status=(200, 201)
        )

    def authenticate(self, payload: Dict[str, Any]) -> ApiResponse:
        return self._request(
            "POST", self._p("auth_login"), json_body=payload, expected_status=200
        )

    def create_video_session(self, token: str, payload: Dict[str, Any]) -> ApiResponse:
        headers = {"Authorization": f"Bearer {token}"}
        return self._request(
            "POST",
            self._p("video_sessions"),
            json_body=payload,
            headers=headers,
            expected_status=201,
        )

    def join_video_session(self, token: str, session_id: str, operator_id: str) -> ApiResponse:
        headers = {"Authorization": f"Bearer {token}"}
        return self._request(
            "POST",
            self._p("video_sessions_join", session_id=session_id),
            json_body={"operator_id": operator_id},
            headers=headers,
            expected_status=200,
        )

    def rate_limited_endpoint(self, token: str) -> ApiResponse:
        headers = {"Authorization": f"Bearer {token}"}
        return self._request("GET", self._p("limits_rate_limited"), headers=headers)


class UserServiceClient(BaseApiClient):
    """Client Object для пользовательского сервиса.

    В большинстве сценариев доступ к нему идёт через API Gateway, но прямой клиент
    может быть полезен для health-check и подготовки данных.
    """

    def health(self) -> ApiResponse:
        return self._request("GET", "/health")


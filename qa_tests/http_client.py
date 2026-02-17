from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, TypeVar, Union

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

        # Используем временную переменную для status, чтобы lambda могла её захватить
        resp_status = "unknown"

        def get_status() -> str:
            return resp_status

        logger.info(
            "HTTP request started",
            extra={
                "method": method.upper(),
                "url": url,
                "path": path,
            },
        )

        with measure_request("api", f"{method.upper()} {path}", get_status):
            resp = requests.request(method, url, json=json_body, headers=merged_headers, timeout=10)
            resp_status = str(resp.status_code)

        if expected_status is not None:
            allowed = (
                (expected_status,) if isinstance(expected_status, int) else tuple(expected_status)
            )
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

    def get(self, path: str, **kwargs: Any) -> ApiResponse:
        """GET запрос по относительному path (например /health, /ready)."""
        return self._request("GET", path, **kwargs)


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
        return str(path.format(**kwargs)) if kwargs else path

    def register_user(self, payload: Dict[str, Any]) -> ApiResponse:
        # User Service возвращает 200, классический REST — 201
        return self._request(
            "POST", self._p("users_register"), json_body=payload, expected_status=(200, 201)
        )

    def authenticate(self, payload: Dict[str, Any]) -> ApiResponse:
        return self._request("POST", self._p("auth_login"), json_body=payload, expected_status=200)

    def auth_refresh(self, payload: Dict[str, Any]) -> ApiResponse:
        return self._request(
            "POST", self._p("auth_refresh"), json_body=payload, expected_status=200
        )

    def auth_logout(self, token: str) -> ApiResponse:
        # Сервис может вернуть 200 или 204
        return self._request(
            "POST",
            self._p("auth_logout"),
            headers={"Authorization": f"Bearer {token}"},
            expected_status=(200, 204),
        )

    def get_me(self, token: str) -> ApiResponse:
        return self._request(
            "GET",
            self._p("users_me"),
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200,
        )

    def update_me(self, token: str, payload: Dict[str, Any]) -> ApiResponse:
        return self._request(
            "PUT",
            self._p("users_me"),
            json_body=payload,
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200,
        )

    def get_user(self, token: str, user_id: str) -> ApiResponse:
        return self._request(
            "GET",
            self._p("users_by_id", id=user_id),
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200,
        )

    def update_user_by_id(self, token: str, user_id: str, payload: Dict[str, Any]) -> ApiResponse:
        return self._request(
            "PUT",
            self._p("users_by_id", id=user_id),
            json_body=payload,
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200,
        )

    def delete_user(self, token: str, user_id: str) -> ApiResponse:
        return self._request(
            "DELETE",
            self._p("users_by_id", id=user_id),
            headers={"Authorization": f"Bearer {token}"},
            expected_status=(200, 204),
        )

    def update_presence(self, token: str, user_id: str, is_online: bool) -> ApiResponse:
        return self._request(
            "PUT",
            self._p("users_presence", user_id=user_id),
            json_body={"is_online": is_online},
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200,
        )

    def list_user_sessions(
        self,
        token: str,
        user_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ApiResponse:
        path = self._p("users_sessions", id=user_id)
        if limit is not None or offset is not None:
            parts = []
            if limit is not None:
                parts.append(f"limit={limit}")
            if offset is not None:
                parts.append(f"offset={offset}")
            path = f"{path}?{'&'.join(parts)}"
        return self._request(
            "GET",
            path,
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200,
        )

    def list_active_sessions(self, token: str, user_id: str) -> ApiResponse:
        return self._request(
            "GET",
            self._p("users_active_sessions", id=user_id),
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200,
        )

    def create_session(self, token: str, user_id: str, payload: Dict[str, Any]) -> ApiResponse:
        # Сервис может вернуть 200 или 201
        return self._request(
            "POST",
            self._p("users_sessions", id=user_id),
            json_body=payload,
            headers={"Authorization": f"Bearer {token}"},
            expected_status=(200, 201),
        )

    def validate_session(self, payload: Dict[str, Any]) -> ApiResponse:
        return self._request(
            "POST",
            self._p("sessions_validate"),
            json_body=payload,
            expected_status=200,
        )

    def operators_available(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ApiResponse:
        path = self._p("operators_available")
        if limit is not None or offset is not None:
            parts = []
            if limit is not None:
                parts.append(f"limit={limit}")
            if offset is not None:
                parts.append(f"offset={offset}")
            path = f"{path}?{'&'.join(parts)}"
        return self._request("GET", path, expected_status=200)

    def operators_availability(self, token: str, available: bool) -> ApiResponse:
        return self._request(
            "PUT",
            self._p("operators_availability"),
            json_body={"available": available},
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200,
        )

    def operators_stats(self) -> ApiResponse:
        return self._request("GET", self._p("operators_stats"), expected_status=200)

    def operators_verify(self, token: str, operator_id: str, status: str) -> ApiResponse:
        return self._request(
            "POST",
            self._p("operators_verify", id=operator_id),
            json_body={"status": status},
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200,
        )

    def operators_availability_by_id(
        self, token: str, user_id: str, is_available: bool
    ) -> ApiResponse:
        return self._request(
            "PUT",
            self._p("operators_availability_by_id", user_id=user_id),
            json_body={"is_available": is_available},
            headers={"Authorization": f"Bearer {token}"},
            expected_status=200,
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
        return self.get("/health")

    def ready(self) -> ApiResponse:
        return self.get("/ready")


class StreamingServiceClient(BaseApiClient):
    """Client Object для микросервиса streaming-service (REST часть).

    Используется для создания/завершения сессий и чтения операторов.
    """

    def health(self) -> ApiResponse:
        return self.get("/health")

    def ready(self) -> ApiResponse:
        return self.get("/ready")

    def create_session(self, client_id: str) -> ApiResponse:
        payload: Dict[str, Any] = {"client_id": client_id}
        # 201 — как указано в README streaming-service
        return self._request("POST", "/sessions", json_body=payload, expected_status=201)

    def delete_session(self, session_id: str) -> ApiResponse:
        return self._request("DELETE", f"/sessions/{session_id}", expected_status=(204, 404))

    def get_session_operators(self, session_id: str) -> ApiResponse:
        return self._request(
            "GET",
            f"/sessions/{session_id}/operators",
            expected_status=(200, 404),
        )


class OperatorDirectoryServiceClient(BaseApiClient):
    """Client для operator-directory-service: /health, /ready, /api/v1/operators (CRUD)."""

    def health(self) -> ApiResponse:
        return self.get("/health")

    def ready(self) -> ApiResponse:
        return self.get("/ready")

    def list_operators(
        self,
        region: Optional[str] = None,
        role: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> ApiResponse:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if region is not None:
            params["region"] = region
        if role is not None:
            params["role"] = role
        if status is not None:
            params["status"] = status
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        path = f"/api/v1/operators?{qs}"
        return self._request("GET", path, expected_status=200)

    def get_operator(self, operator_id: str) -> ApiResponse:
        return self._request(
            "GET",
            f"/api/v1/operators/{operator_id}",
            expected_status=(200, 400, 404),
        )

    def create_operator(self, payload: Dict[str, Any]) -> ApiResponse:
        return self._request(
            "POST",
            "/api/v1/operators",
            json_body=payload,
            expected_status=(201, 400, 409),
        )

    def update_operator(self, operator_id: str, payload: Dict[str, Any]) -> ApiResponse:
        return self._request(
            "PUT",
            f"/api/v1/operators/{operator_id}",
            json_body=payload,
            expected_status=(200, 400, 404),
        )


class OperatorPoolServiceClient(BaseApiClient):
    """Client для operator-pool-service: /health, /ready, /operator/status, next, stats, list."""

    def health(self) -> ApiResponse:
        return self.get("/health")

    def ready(self) -> ApiResponse:
        return self.get("/ready")

    def set_status(self, payload: Dict[str, Any]) -> ApiResponse:
        """POST /operator/status — user_id, available, max_sessions."""
        return self._request(
            "POST",
            "/operator/status",
            json_body=payload,
            expected_status=(200, 400, 500),
        )

    def next_operator(self) -> ApiResponse:
        """GET /operator/next — 200 { operator_id } или 404."""
        return self._request("GET", "/operator/next", expected_status=(200, 404, 500))

    def stats(self) -> ApiResponse:
        """GET /operator/stats — 200 { available, total }."""
        return self._request("GET", "/operator/stats", expected_status=(200, 500))

    def list_operators(self) -> ApiResponse:
        """GET /operator/list — 200 { operators: [...] }."""
        return self._request("GET", "/operator/list", expected_status=(200, 500))


class NotificationServiceClient(BaseApiClient):
    """Client для notification-service: /health, /ready, POST /notify/session/:id."""

    def health(self) -> ApiResponse:
        return self.get("/health")

    def ready(self) -> ApiResponse:
        return self.get("/ready")

    def notify_session(self, session_id: str, payload: Dict[str, Any]) -> ApiResponse:
        """POST /notify/session/:id — body: event (required), payload (optional)."""
        return self._request(
            "POST",
            f"/notify/session/{session_id}",
            json_body=payload,
            expected_status=(200, 400),
        )


class SearchServiceClient(BaseApiClient):
    """Client для search-service: /health, /ready, GET /search, POST /search/index/*."""

    def health(self) -> ApiResponse:
        return self.get("/health")

    def ready(self) -> ApiResponse:
        return self.get("/ready")

    def search(
        self,
        query: str,
        type_filter: Optional[str] = None,
        limit: int = 20,
    ) -> ApiResponse:
        """GET /search?q=...&type=tickets|sessions|operators|all&limit=20."""
        params: Dict[str, Any] = {"q": query, "limit": limit}
        if type_filter is not None:
            params["type"] = type_filter
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        path = f"/search?{qs}"
        return self._request("GET", path, expected_status=(200, 500))

    def index_ticket(self, payload: Dict[str, Any]) -> ApiResponse:
        """POST /search/index/ticket."""
        return self._request(
            "POST",
            "/search/index/ticket",
            json_body=payload,
            expected_status=(200, 400, 500),
        )

    def index_session(self, payload: Dict[str, Any]) -> ApiResponse:
        """POST /search/index/session."""
        return self._request(
            "POST",
            "/search/index/session",
            json_body=payload,
            expected_status=(200, 400, 500),
        )

    def index_operator(self, payload: Dict[str, Any]) -> ApiResponse:
        """POST /search/index/operator."""
        return self._request(
            "POST",
            "/search/index/operator",
            json_body=payload,
            expected_status=(200, 400, 500),
        )


class TicketServiceClient(BaseApiClient):
    """Client для ticket-service: /health, /ready, /api/v1/tickets (CRUD)."""

    def health(self) -> ApiResponse:
        return self.get("/health")

    def ready(self) -> ApiResponse:
        return self.get("/ready")

    def create_ticket(self, payload: Dict[str, Any]) -> ApiResponse:
        """POST /api/v1/tickets — возвращает 201 Created."""
        return self._request(
            "POST",
            "/api/v1/tickets",
            json_body=payload,
            expected_status=(201, 400, 500),
        )

    def get_ticket(self, ticket_id: str) -> ApiResponse:
        """GET /api/v1/tickets/:id — id должен быть числом (uint64)."""
        return self._request(
            "GET",
            f"/api/v1/tickets/{ticket_id}",
            expected_status=(200, 400, 404, 500),
        )

    def list_tickets(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> ApiResponse:
        """GET /api/v1/tickets?limit=...&offset=..."""
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        path = f"/api/v1/tickets?{qs}" if qs else "/api/v1/tickets"
        return self._request("GET", path, expected_status=(200, 500))

    def update_ticket(self, ticket_id: str, payload: Dict[str, Any]) -> ApiResponse:
        """PUT /api/v1/tickets/:id — id должен быть числом (uint64)."""
        return self._request(
            "PUT",
            f"/api/v1/tickets/{ticket_id}",
            json_body=payload,
            expected_status=(200, 400, 404, 500),
        )


class DataChannelServiceClient(BaseApiClient):
    """Client для data-channel-service: /health, /ready, GET /data/:session_id/history, POST /data/file."""  # noqa: E501

    def health(self) -> ApiResponse:
        return self.get("/health")

    def ready(self) -> ApiResponse:
        return self.get("/ready")

    def get_history(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> ApiResponse:
        """GET /data/:session_id/history?limit=..."""
        params: Dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        path = f"/data/{session_id}/history?{qs}" if qs else f"/data/{session_id}/history"
        return self._request("GET", path, expected_status=(200, 400, 500))

    def upload_file(
        self,
        session_id: str,
        user_id: str,
        file_path: str,
        filename: Optional[str] = None,
    ) -> ApiResponse:
        """POST /data/file — multipart/form-data с session_id, user_id, file."""
        url = self._url("/data/file")
        if filename is None:
            from pathlib import Path

            filename = Path(file_path).name

        with open(file_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            data = {"session_id": session_id, "user_id": user_id}

            resp_status = "unknown"

            def get_status() -> str:
                return resp_status

            logger.info(
                "HTTP request started",
                extra={
                    "method": "POST",
                    "url": url,
                    "path": "/data/file",
                },
            )

            with measure_request("api", "POST /data/file", get_status):
                resp = requests.post(url, files=files, data=data, timeout=30)
                resp_status = str(resp.status_code)

        try:
            payload = resp.json()
        except ValueError:
            payload = None

        return ApiResponse(status_code=resp.status_code, json=payload, raw=resp)

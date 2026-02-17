from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv


class TestEnv(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


@dataclass(frozen=True)
class ServiceConfig:
    base_url: str


@dataclass(frozen=True)
class WebSocketConfig:
    base_url: str


@dataclass(frozen=True)
class JiraConfig:
    base_url: str
    project_key: str
    username: str
    api_token: str


@dataclass(frozen=True)
class SlackConfig:
    webhook_url: str


@dataclass(frozen=True)
class TeamsConfig:
    webhook_url: str


@dataclass(frozen=True)
class DbConfig:
    host: str
    port: int
    name: str
    user: str
    password: str


@dataclass(frozen=True)
class ApiPaths:
    """Пути эндпоинтов API. Задаются через env для совместимости с разными версиями gateway."""

    users_register: str
    auth_login: str
    auth_refresh: str
    auth_logout: str
    users_me: str
    users_by_id: str  # /api/v1/users/{id}
    users_presence: str  # /api/v1/users/{user_id}/presence
    users_sessions: str  # /api/v1/users/{id}/sessions
    users_active_sessions: str  # /api/v1/users/{id}/active-sessions
    sessions_validate: str
    operators_available: str
    operators_availability: str  # PUT /api/v1/operators/availability
    operators_stats: str
    operators_verify: str  # /api/v1/operators/{id}/verify
    operators_availability_by_id: str  # /api/v1/operators/{user_id}/availability
    video_sessions: str
    video_sessions_join: str
    limits_rate_limited: str


@dataclass(frozen=True)
class Settings:
    env: TestEnv
    api_gateway: ServiceConfig
    user_service: ServiceConfig
    streaming_service: ServiceConfig
    operator_directory_service: ServiceConfig
    operator_pool_service: ServiceConfig
    notification_service: ServiceConfig
    notification_ws: WebSocketConfig
    search_service: ServiceConfig
    websocket: WebSocketConfig
    streaming_ws: WebSocketConfig
    api_paths: ApiPaths
    allure_results_dir: Path
    jira: Optional[JiraConfig]
    slack: Optional[SlackConfig]
    teams: Optional[TeamsConfig]
    db: Optional[DbConfig]
    rate_limit_test_user: Optional[str]


def _load_dotenv() -> None:
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    load_dotenv(dotenv_path=env_path, override=False)


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    import os

    return os.getenv(name, default)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Загружает и кэширует настройки фреймворка из окружения и .env."""
    _load_dotenv()

    env_raw = _get_env("TEST_ENV", "local")
    env: Literal["local", "dev", "staging", "prod"]
    if env_raw not in {e.value for e in TestEnv}:
        env = "local"
    else:
        env = env_raw  # type: ignore[assignment]

    api_gateway_base = (
        _get_env("API_GATEWAY_BASE_URL", "http://localhost:8080") or "http://localhost:8080"
    )
    user_service_base = _get_env("USER_SERVICE_BASE_URL", api_gateway_base) or api_gateway_base
    websocket_base = _get_env("WEBSOCKET_BASE_URL", "ws://localhost:8080") or "ws://localhost:8080"
    streaming_base = (
        _get_env("STREAMING_SERVICE_BASE_URL", "http://localhost:8090") or "http://localhost:8090"
    )
    streaming_ws_base = (
        _get_env("STREAMING_WS_BASE_URL", "ws://localhost:8090") or "ws://localhost:8090"
    )
    operator_directory_base = (
        _get_env("OPERATOR_DIRECTORY_SERVICE_BASE_URL", "http://localhost:8095")
        or "http://localhost:8095"
    )
    operator_pool_base = (
        _get_env("OPERATOR_POOL_SERVICE_BASE_URL", "http://localhost:8094")
        or "http://localhost:8094"
    )
    notification_base = (
        _get_env("NOTIFICATION_SERVICE_BASE_URL", "http://localhost:8092")
        or "http://localhost:8092"
    )
    notification_ws_base = (
        _get_env("NOTIFICATION_WS_BASE_URL", "ws://localhost:8092") or "ws://localhost:8092"
    )
    search_base = (
        _get_env("SEARCH_SERVICE_BASE_URL", "http://localhost:8096") or "http://localhost:8096"
    )

    allure_dir_raw = _get_env("ALLURE_RESULTS_DIR", "allure-results")
    allure_dir = Path(allure_dir_raw or "allure-results").resolve()

    jira_base = _get_env("JIRA_BASE_URL")
    jira_project_key = _get_env("JIRA_PROJECT_KEY")
    jira_username = _get_env("JIRA_USERNAME")
    jira_token = _get_env("JIRA_API_TOKEN")
    jira = (
        JiraConfig(
            base_url=jira_base,
            project_key=jira_project_key or "",
            username=jira_username or "",
            api_token=jira_token or "",
        )
        if jira_base and jira_project_key and jira_username and jira_token
        else None
    )

    slack_webhook = _get_env("SLACK_WEBHOOK_URL")
    slack = SlackConfig(webhook_url=slack_webhook) if slack_webhook else None

    teams_webhook = _get_env("TEAMS_WEBHOOK_URL")
    teams = TeamsConfig(webhook_url=teams_webhook) if teams_webhook else None

    db_host = _get_env("DB_HOST")
    db_port = _get_env("DB_PORT")
    db_name = _get_env("DB_NAME")
    db_user = _get_env("DB_USER")
    db_password = _get_env("DB_PASSWORD")
    db = (
        DbConfig(
            host=db_host or "localhost",
            port=int(db_port or "5432"),
            name=db_name or "psds_test",
            user=db_user or "psds",
            password=db_password or "psds",
        )
        if db_host or db_name
        else None
    )

    rate_limit_user = _get_env("RATE_LIMIT_TEST_USER")

    def _path(key: str, default: str) -> str:
        return _get_env(key, default) or default

    api_paths = ApiPaths(
        users_register=_path("API_USERS_REGISTER_PATH", "/api/v1/auth/register"),
        auth_login=_path("API_AUTH_LOGIN_PATH", "/api/v1/auth/login"),
        auth_refresh=_path("API_AUTH_REFRESH_PATH", "/api/v1/auth/refresh"),
        auth_logout=_path("API_AUTH_LOGOUT_PATH", "/api/v1/auth/logout"),
        users_me=_path("API_USERS_ME_PATH", "/api/v1/users/me"),
        users_by_id=_path("API_USERS_BY_ID_PATH", "/api/v1/users/{id}"),
        users_presence=_path("API_USERS_PRESENCE_PATH", "/api/v1/users/{user_id}/presence"),
        users_sessions=_path("API_USERS_SESSIONS_PATH", "/api/v1/users/{id}/sessions"),
        users_active_sessions=_path(
            "API_USERS_ACTIVE_SESSIONS_PATH", "/api/v1/users/{id}/active-sessions"
        ),
        sessions_validate=_path("API_SESSIONS_VALIDATE_PATH", "/api/v1/sessions/validate"),
        operators_available=_path("API_OPERATORS_AVAILABLE_PATH", "/api/v1/operators/available"),
        operators_availability=_path(
            "API_OPERATORS_AVAILABILITY_PATH", "/api/v1/operators/availability"
        ),
        operators_stats=_path("API_OPERATORS_STATS_PATH", "/api/v1/operators/stats"),
        operators_verify=_path("API_OPERATORS_VERIFY_PATH", "/api/v1/operators/{id}/verify"),
        operators_availability_by_id=_path(
            "API_OPERATORS_AVAILABILITY_BY_ID_PATH",
            "/api/v1/operators/{user_id}/availability",
        ),
        video_sessions=_path("API_VIDEO_SESSIONS_PATH", "/v1/video/sessions"),
        video_sessions_join=_path(
            "API_VIDEO_SESSIONS_JOIN_PATH", "/v1/video/sessions/{session_id}/join"
        ),
        limits_rate_limited=_path("API_LIMITS_RATE_LIMITED_PATH", "/v1/limits/rate-limited"),
    )

    return Settings(
        env=TestEnv(env),
        api_gateway=ServiceConfig(base_url=api_gateway_base),
        user_service=ServiceConfig(base_url=user_service_base),
        streaming_service=ServiceConfig(base_url=streaming_base),
        operator_directory_service=ServiceConfig(base_url=operator_directory_base),
        operator_pool_service=ServiceConfig(base_url=operator_pool_base),
        notification_service=ServiceConfig(base_url=notification_base),
        notification_ws=WebSocketConfig(base_url=notification_ws_base),
        search_service=ServiceConfig(base_url=search_base),
        websocket=WebSocketConfig(base_url=websocket_base),
        streaming_ws=WebSocketConfig(base_url=streaming_ws_base),
        api_paths=api_paths,
        allure_results_dir=allure_dir,
        jira=jira,
        slack=slack,
        teams=teams,
        db=db,
        rate_limit_test_user=rate_limit_user,
    )

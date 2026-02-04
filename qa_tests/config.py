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
    video_sessions: str
    video_sessions_join: str
    limits_rate_limited: str


@dataclass(frozen=True)
class Settings:
    env: TestEnv
    api_gateway: ServiceConfig
    user_service: ServiceConfig
    websocket: WebSocketConfig
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

    api_gateway_base = _get_env("API_GATEWAY_BASE_URL", "http://localhost:8080")
    user_service_base = _get_env("USER_SERVICE_BASE_URL", api_gateway_base)
    websocket_base = _get_env("WEBSOCKET_BASE_URL", "ws://localhost:8080")

    allure_dir_raw = _get_env("ALLURE_RESULTS_DIR", "allure-results")
    allure_dir = Path(allure_dir_raw).resolve()

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

    api_paths = ApiPaths(
        users_register=_get_env("API_USERS_REGISTER_PATH", "/api/v1/auth/register"),
        auth_login=_get_env("API_AUTH_LOGIN_PATH", "/api/v1/auth/login"),
        video_sessions=_get_env("API_VIDEO_SESSIONS_PATH", "/v1/video/sessions"),
        video_sessions_join=_get_env(
            "API_VIDEO_SESSIONS_JOIN_PATH", "/v1/video/sessions/{session_id}/join"
        ),
        limits_rate_limited=_get_env("API_LIMITS_RATE_LIMITED_PATH", "/v1/limits/rate-limited"),
    )

    return Settings(
        env=TestEnv(env),
        api_gateway=ServiceConfig(base_url=api_gateway_base),
        user_service=ServiceConfig(base_url=user_service_base),
        websocket=WebSocketConfig(base_url=websocket_base),
        api_paths=api_paths,
        allure_results_dir=allure_dir,
        jira=jira,
        slack=slack,
        teams=teams,
        db=db,
        rate_limit_test_user=rate_limit_user,
    )


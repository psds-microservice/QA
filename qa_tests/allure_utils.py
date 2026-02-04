from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

import allure

from .config import get_settings


def attach_text(name: str, body: str, attachment_type: allure.attachment_type = allure.attachment_type.TEXT) -> None:
    """Простой helper для текстовых вложений в Allure."""
    allure.attach(body, name=name, attachment_type=attachment_type)


def attach_json(name: str, body: str) -> None:
    attach_text(name, body, attachment_type=allure.attachment_type.JSON)


def attach_screenshot(name: str, path: Path) -> None:
    """Прикрепляет скриншот/кадр видео по пути."""
    if path.exists():
        allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)


@contextmanager
def allure_step(name: str) -> Iterator[None]:
    """Контекстный менеджер для шагов Allure."""
    with allure.step(name):
        yield


def link_jira(issue_key: str) -> None:
    """Добавляет ссылку на JIRA-тикет в отчёт Allure."""
    settings = get_settings()
    if settings.jira:
        url = f"{settings.jira.base_url.rstrip('/')}/browse/{issue_key}"
        allure.dynamic.link(url, name=issue_key, link_type="jira")


def mark_story(story: str) -> None:
    allure.dynamic.story(story)


def mark_feature(feature: str) -> None:
    allure.dynamic.feature(feature)


def mark_severity(level: Optional[str] = "normal") -> None:
    from allure_commons.types import Severity

    mapping = {
        "blocker": Severity.BLOCKER,
        "critical": Severity.CRITICAL,
        "normal": Severity.NORMAL,
        "minor": Severity.MINOR,
        "trivial": Severity.TRIVIAL,
    }
    allure.dynamic.severity(mapping.get(level or "normal", Severity.NORMAL))


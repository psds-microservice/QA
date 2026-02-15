from __future__ import annotations

import json

import allure
import pytest
import requests

from qa_tests.allure_utils import (
    allure_step,
    attach_json,
    link_jira,
    mark_feature,
    mark_severity,
    mark_story,
)


@pytest.mark.smoke
@allure.tag("contract", "openapi", "user-service")
def test_openapi_contract_exposed_and_valid(settings) -> None:
    """Сервис (User Service или gateway) публикует OpenAPI с путями auth.
    Набор test-user-service-local. Контракт gateway — test_api_gateway.py.
    """
    mark_feature("API Contracts")
    mark_story("Экспонирование OpenAPI/Swagger")
    mark_severity("critical")
    link_jira("PSDS-501")

    with allure_step("Получение OpenAPI контракта"):
        url_candidates = [
            f"{settings.api_gateway.base_url.rstrip('/')}/openapi.json",
            f"{settings.api_gateway.base_url.rstrip('/')}/swagger/doc.json",
        ]
        last_resp = None
        for url in url_candidates:
            try:
                resp = requests.get(url, timeout=5)
                last_resp = resp
                if resp.status_code == 200:
                    break
            except Exception:
                continue

        assert last_resp is not None, "Не удалось получить OpenAPI контракт ни по одному из URL"
        assert last_resp.status_code == 200, f"Unexpected status code {last_resp.status_code}"
        spec = last_resp.json()
        attach_json("openapi_spec", json.dumps(spec, ensure_ascii=False)[:5000])

    with allure_step("Валидация базовой структуры OpenAPI"):
        assert "openapi" in spec or "swagger" in spec
        assert "paths" in spec and isinstance(spec["paths"], dict)
        # Пример проверки наличия ключевых эндпоинтов
        expected_paths = ["/api/v1/auth/register", "/api/v1/auth/login"]
        missing = [p for p in expected_paths if p not in spec["paths"]]
        assert not missing, f"В OpenAPI отсутствуют ожидаемые пути: {missing}"

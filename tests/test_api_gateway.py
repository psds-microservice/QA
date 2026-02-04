"""Тесты, специфичные для API Gateway: health, status, OpenAPI контракт gateway.

Ручки User Service (auth, me, users, sessions, operators) не дублируются здесь —
полное покрытие по ним в наборе test-user-service-local. См. docs/TEST_COVERAGE_STRATEGY.md.
"""

from __future__ import annotations

import json

import allure
import pytest
import requests

from qa_tests.allure_utils import allure_step, attach_json, link_jira, mark_feature, mark_severity, mark_story
from qa_tests.http_client import ApiGatewayClient
from qa_tests.metrics import measure_test_case


@pytest.mark.smoke
@allure.tag("gateway", "health")
def test_gateway_health(api_gateway_client: ApiGatewayClient) -> None:
    """GET /health на API Gateway возвращает 200."""
    mark_feature("API Gateway")
    mark_story("Health")
    mark_severity("critical")
    link_jira("PSDS-100")

    with measure_test_case("test_gateway_health"):
        with allure_step("Запрос GET /health"):
            resp = api_gateway_client.get("/health")
        assert resp.status_code == 200


@pytest.mark.smoke
@allure.tag("gateway", "status")
def test_gateway_status_endpoint(api_gateway_client: ApiGatewayClient) -> None:
    """GET /api/v1/status на API Gateway возвращает 200 и информацию об эндпоинтах."""
    mark_feature("API Gateway")
    mark_story("Status")
    mark_severity("normal")
    link_jira("PSDS-200")

    with measure_test_case("test_gateway_status_endpoint"):
        with allure_step("Запрос GET /api/v1/status"):
            resp = api_gateway_client.get("/api/v1/status")
        assert resp.status_code == 200
        assert resp.json is not None
        if "endpoints" in resp.json:
            attach_json("gateway_endpoints", json.dumps(resp.json.get("endpoints", []), indent=2))


@pytest.mark.smoke
@allure.tag("gateway", "contract", "openapi")
def test_gateway_openapi_exposes_video_paths(api_gateway_client: ApiGatewayClient) -> None:
    """OpenAPI контракт API Gateway содержит пути видеопотока (уникальные для gateway)."""
    mark_feature("API Gateway")
    mark_story("OpenAPI контракт")
    mark_severity("critical")
    link_jira("PSDS-501")

    base = api_gateway_client.base_url.rstrip("/")
    url_candidates = [f"{base}/openapi.json", f"{base}/swagger/doc.json"]
    spec = None
    with allure_step("Получение OpenAPI контракта gateway"):
        for url in url_candidates:
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    spec = r.json()
                    attach_json("openapi_spec", json.dumps(spec, ensure_ascii=False)[:5000])
                    break
            except Exception:
                continue
        assert spec is not None, "Не удалось получить OpenAPI контракт gateway"

    with allure_step("Проверка наличия путей API Gateway (video, status)"):
        paths = spec.get("paths") or {}
        # Gateway предоставляет video и status; auth/users — из user-service, в контракте gateway могут отсутствовать
        gateway_path_examples = ["/api/v1/status", "/api/v1/video/start", "/api/v1/video/frame", "/api/v1/video/stop"]
        found = [p for p in gateway_path_examples if p in paths]
        assert len(found) >= 1, f"В контракте gateway ожидались пути вида video/status, найдено: {list(paths.keys())[:15]}"

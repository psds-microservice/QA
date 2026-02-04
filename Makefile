PYTHON ?= python

VENV_DIR := .venv

.PHONY: help bootstrap test-local test-with-docker test-api-gateway-local test-user-service-local

help:
	@echo "Доступные команды:"
	@echo "  make bootstrap               - подготовить проект (venv, зависимости, .env, pre-commit)"
	@echo "  make test-local              - запустить все локальные тесты (с уже запущенными сервисами)"
	@echo "  make test-with-docker        - поднять docker-compose.test.yml и запустить все тесты"
	@echo "  make test-api-gateway-local  - запустить только тесты для API Gateway"
	@echo "  make test-user-service-local - запустить только тесты для User Service"

bootstrap:
	@echo "==> Создание виртуального окружения (если нет)"
	if not exist "$(VENV_DIR)" $(PYTHON) -m venv $(VENV_DIR)
	@echo "==> Установка/обновление pip"
	@$(PYTHON) -m pip install --upgrade pip
	@echo "==> Установка зависимостей проекта (включая dev)"
	@$(PYTHON) -m pip install .[dev]
	@echo "==> Создание .env из .env.example (если нет)"
	if not exist ".env" if exist ".env.example" copy /Y .env.example .env
	@echo "==> Установка pre-commit хуков"
	@pre-commit install || exit 0

test-local:
	@echo "==> Запуск всех локальных тестов (с уже работающим api-gateway/user-service)"
	@$(PYTHON) -m pytest

test-with-docker:
	@echo "==> Поднимаем docker-compose.test.yml"
	docker compose -f docker-compose.test.yml up -d --build
	@echo "==> Запускаем тесты"
	@$(PYTHON) -m pytest
	@echo "==> Останавливаем docker-compose.test.yml"
	docker compose -f docker-compose.test.yml down

test-api-gateway-local:
	@echo "==> Локальные тесты, фокус на API Gateway (без дублирования ручек User Service)"
	@$(PYTHON) -m pytest \
		tests/test_api_gateway.py \
		tests/test_rate_limiting.py

test-user-service-local:
	@echo "==> Локальные тесты, фокус на User Service"
	@$(PYTHON) -m pytest \
		tests/test_health_user_service.py \
		tests/test_auth_flow.py \
		tests/test_validation_negative.py \
		tests/test_me_user_service.py \
		tests/test_users_user_service.py \
		tests/test_sessions_user_service.py \
		tests/test_operators_user_service.py


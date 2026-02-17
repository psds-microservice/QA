PYTHON ?= python

VENV_DIR := .venv

.PHONY: help bootstrap test-local test-with-docker test-api-gateway-local test-user-service-local test-streaming-service-local test-operator-directory-service-local test-operator-pool-service-local test-notification-service-local test-search-service-local test-ticket-service-local test-data-channel-service-local test-session-manager-service-local

help:
	@echo "Доступные команды:"
	@echo "  make bootstrap               - подготовить проект (venv, зависимости, .env, pre-commit)"
	@echo "  make test-local              - запустить все локальные тесты (с уже запущенными сервисами)"
	@echo "  make test-with-docker        - поднять docker-compose.test.yml и запустить все тесты"
	@echo "  make test-api-gateway-local  - запустить только тесты для API Gateway"
	@echo "  make test-user-service-local - запустить только тесты для User Service"
	@echo "  make test-streaming-service-local - запустить только тесты для Streaming Service"
	@echo "  make test-operator-directory-service-local - только тесты Operator Directory Service"
	@echo "  make test-operator-pool-service-local - только тесты Operator Pool Service"
	@echo "  make test-notification-service-local - только тесты Notification Service"
	@echo "  make test-search-service-local - только тесты Search Service"
	@echo "  make test-ticket-service-local - только тесты Ticket Service"
	@echo "  make test-data-channel-service-local - только тесты Data Channel Service"
	@echo "  make test-session-manager-service-local - только тесты Session Manager Service"

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
	@$(PYTHON) -m pytest -p no:xdist \
		tests/test_api_gateway.py \
		tests/test_rate_limiting.py

test-user-service-local:
	@echo "==> Локальные тесты, фокус на User Service"
	@$(PYTHON) -m pytest -p no:xdist \
		tests/test_health_user_service.py \
		tests/test_auth_flow.py \
		tests/test_validation_negative.py \
		tests/test_me_user_service.py \
		tests/test_users_user_service.py \
		tests/test_sessions_user_service.py \
		tests/test_operators_user_service.py

test-streaming-service-local:
	@echo "==> Local tests, focus on Streaming Service"
	@$(PYTHON) -m pytest -p no:xdist \
		tests/test_streaming_health.py \
		tests/test_streaming_sessions_rest.py \
		tests/test_streaming_websocket.py

test-operator-directory-service-local:
	@echo "==> Local tests, focus on Operator Directory Service"
	@$(PYTHON) -m pytest -p no:xdist \
		tests/test_operator_directory_health.py \
		tests/test_operator_directory_rest.py

test-operator-pool-service-local:
	@echo "==> Local tests, focus on Operator Pool Service"
	@$(PYTHON) -m pytest -p no:xdist \
		tests/test_operator_pool_health.py \
		tests/test_operator_pool_rest.py

test-notification-service-local:
	@echo "==> Local tests, focus on Notification Service"
	@$(PYTHON) -m pytest -p no:xdist \
		tests/test_notification_health.py \
		tests/test_notification_rest.py \
		tests/test_notification_websocket.py

test-search-service-local:
	@echo "==> Local tests, focus on Search Service"
	@$(PYTHON) -m pytest -p no:xdist \
		tests/test_search_health.py \
		tests/test_search_rest.py

test-ticket-service-local:
	@echo "==> Local tests, focus on Ticket Service"
	@$(PYTHON) -m pytest -p no:xdist \
		tests/test_ticket_health.py \
		tests/test_ticket_rest.py

test-data-channel-service-local:
	@echo "==> Local tests, focus on Data Channel Service"
	@$(PYTHON) -m pytest -p no:xdist \
		tests/test_data_channel_health.py \
		tests/test_data_channel_rest.py

test-session-manager-service-local:
	@echo "==> Local tests, focus on Session Manager Service"
	@$(PYTHON) -m pytest -p no:xdist \
		tests/test_session_manager_health.py \
		tests/test_session_manager_rest.py

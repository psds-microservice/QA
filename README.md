## PSDS QA E2E Framework

End-to-end фреймворк для тестирования микросервисной системы видеоконсультирования (API Gateway, User Service, Python Client и будущие сервисы операторов).

### Возможности

- **Технологии**: Python 3.10+, `pytest`, `pytest-asyncio`, `pytest-docker`, `pytest-xdist`, `allure-pytest`, `requests`, `websockets`, `pydantic`, `Faker`, `python-dotenv`, `grpcio`.
- **Архитектура**:
  - **Client Object** для HTTP (`ApiGatewayClient`, `UserServiceClient`) и WebSocket (`WebSocketClient`).
  - Поддержка **gRPC** через конфигурируемый `GrpcClient` (стабы из протопакетов репозиториев).
  - Чёткое разделение на `qa_tests/` (фреймворк) и `tests/` (сценарии).
  - Общие фикстуры и плагины (`qa_tests/fixtures.py`, `conftest.py`).
- **Отчётность и интеграции**:
  - Allure steps, attachments, аннотации.
  - Логирование в JSON (`qa_tests/logging_utils.py`).
  - Метрики времени (`qa_tests/metrics.py`) на базе Prometheus client.
- **Инфраструктура**:
  - `docker-compose.test.yml` для запуска api-gateway, user-service, mitmproxy.
  - Возможность запуска против удалённого окружения через `.env`.
  - pre-commit хуки, mypy/black/isort/flake8.

### Структура проекта

- `qa_tests/` – ядро фреймворка:
  - `config.py` – загрузка конфигурации и окружения (`.env`, переменные среды).
  - `logging_utils.py` – JSON-логирование.
  - `metrics.py` – метрики тестов и запросов.
  - `retry.py` – retry-механизм для flaky вызовов.
  - `models.py` – pydantic-модели DTO.
  - `http_client.py` – Client Object для REST API.
  - `ws_client.py` – WebSocket клиент.
  - `grpc_client.py` – базовый gRPC-клиент.
  - `allure_utils.py` – helper’ы для шагов и вложений Allure.
  - `data_factory.py` – генерация тестовых данных (Faker).
  - `fixtures.py` – общие pytest-фикстуры.
- `tests/` – e2e-сценарии:
  - `test_auth_flow.py` – регистрация и аутентификация.
  - `test_video_session_realtime.py` – видеосессия + WebSocket чат.
  - `test_rate_limiting.py` – rate limiting на API Gateway.
  - `test_validation_negative.py` – негативные сценарии валидации.
  - `test_openapi_contracts.py` – проверка OpenAPI/Swagger контракта.

### Установка

```bash
cd psds/qa
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install .[dev]
pre-commit install
```

### Настройка окружения

Создайте `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

Ключевые переменные:

- **Окружение**:
  - `TEST_ENV=local|dev|staging|prod`
- **REST/gRPC endpoints**:
  - `API_GATEWAY_BASE_URL=http://localhost:8080`
  - `USER_SERVICE_BASE_URL=http://localhost:8080`
  - `WEBSOCKET_BASE_URL=ws://localhost:8080`
  - `API_GATEWAY_GRPC_ADDRESS=localhost:9090`
  - `API_GATEWAY_GRPC_PROTO_MODULE=video.v1.video_service_pb2_grpc`
  - `API_GATEWAY_GRPC_STUB_CLASS=VideoServiceStub`
- **Интеграции**:
  - `JIRA_BASE_URL`, `JIRA_PROJECT_KEY`, `JIRA_USERNAME`, `JIRA_API_TOKEN`
  - `SLACK_WEBHOOK_URL`, `TEAMS_WEBHOOK_URL`
- **База данных**:
  - `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

### Подключение gRPC протоколов из репозиториев

1. Синхронизируйте `.proto` файлы из `api-gateway`/`user-service` (или общего репозитория контрактов) в отдельный каталог, например `protos/`.
2. Сгенерируйте Python-стабы, например:

```bash
python -m grpc_tools.protoc \
  -I protos \
  --python_out=protos \
  --grpc_python_out=protos \
  protos/video/v1/video_service.proto
```

3. Убедитесь, что `protos/` добавлен в `PYTHONPATH` (или используйте `sys.path` внутри тестов).
4. Задайте в `.env`:

```bash
API_GATEWAY_GRPC_ADDRESS=localhost:9090
API_GATEWAY_GRPC_PROTO_MODULE=video.v1.video_service_pb2_grpc
API_GATEWAY_GRPC_STUB_CLASS=VideoServiceStub
```

Теперь вы можете создавать gRPC-клиент на базе `qa_tests/grpc_client.py` и писать e2e-тесты, которые используют реальные контрактные стабы из ваших Go-сервисов.

### Запуск локально

#### 1. Локальный стек через docker-compose

```bash
docker compose -f docker-compose.test.yml up -d --build
pytest
```

`pytest-docker` и фикстура `wait_for_services` автоматически подождут health-check `api-gateway` перед запуском тестов.

#### 2. Против удалённого окружения

- Не запускайте `docker-compose.test.yml`.
- Укажите реальные URL сервисов в `.env` (`*_BASE_URL`, `*_ADDRESS`).
- Запустите:

```bash
pytest
```

### Примеры ключевых тестов

- **Регистрация и аутентификация** – `tests/test_auth_flow.py`
- **Создание видеосессии и обмен сообщениями по WebSocket** – `tests/test_video_session_realtime.py`
- **Rate limiting на API Gateway** – `tests/test_rate_limiting.py`
- **Негативная валидация входных данных** – `tests/test_validation_negative.py`
- **Проверка OpenAPI/Swagger контракта** – `tests/test_openapi_contracts.py`

Каждый тест использует:

- **Allure steps и вложения** (`allure_step`, `attach_json`, ссылки на JIRA);
- **pydantic-модели** для строгой валидации DTO;
- **метрики времени** (`measure_test_case`) и логирование в JSON.

### Параллельный запуск и flaky тесты

- Параллельный запуск включён по умолчанию через `pytest-xdist` (`-n auto` в `pytest.ini`/`pyproject.toml`).
- Для flaky тестов можно использовать `pytest-rerunfailures`:

```bash
pytest --reruns 2 --reruns-delay 5
```

### Качество кода

- **Типизация**: строгий `mypy` (`[tool.mypy]` в `pyproject.toml`).
- **Форматирование**: `black`, `isort`.
- **Линтеры**: `flake8`, `pylint` при необходимости.
- **pre-commit**: `.pre-commit-config.yaml` запускает форматтеры и mypy перед коммитом.

### Allure-отчёты

- Локально:

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

- В CI:
  - Allure-результаты и HTML-отчёт сохраняются как артефакты (`allure-results`, `allure-report`).
  - Историю запусков можно хранить, скачивая артефакты предыдущих запусков и копируя директорию `history` в новые `allure-results` перед генерацией отчёта.

### CI (GitHub Actions)

- Workflow `ci.yml`:
  - Устанавливает зависимости.
  - Поднимает `docker-compose.test.yml`.
  - Дожидается health-check.
  - Запускает `pytest` с генерацией Allure-результатов.
  - Публикует артефакты отчёта.
- Интеграция с Slack/Teams и JIRA/Xray настраивается через:
  - webhooks (`SLACK_WEBHOOK_URL`, `TEAMS_WEBHOOK_URL`);
  - экспорт Allure-результатов и их загрузку в Xray/JIRA (через отдельный скрипт или CI-джобу).

### Расширение под новые сервисы

- Добавьте новый **Client Object** в `qa_tests/` (например, `operator_service_client.py`).
- Опишите pydantic-модели запросов/ответов в `models.py` или отдельном модуле.
- Добавьте фикстуры для клиента и, при необходимости, подготовки тестовых данных.
- Реализуйте e2e-сценарии в `tests/` в духе существующих тестов (Allure, метрики, валидация контрактов).


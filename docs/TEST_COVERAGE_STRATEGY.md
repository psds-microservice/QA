# Стратегия покрытия: API Gateway vs User Service

Чтобы не дублировать проверки одних и тех же ручек, тесты разделены по **целевому сервису** и по **роли** (уникальная логика сервиса vs прокси).

---

## Принцип: без дублирования ручек

- **User Service** — единственный источник правды по пользователям, auth, сессиям, операторам. Все сценарии (позитивные и негативные) по этим ручкам проверяются **только в наборе тестов User Service**.
- **API Gateway** проверяется только по тому, что он **добавляет сам**: health, статус, видеопотоки, rate limiting, свой OpenAPI. Ручки, которые gateway просто проксирует в User Service, **не перепокрываются** полным набором тестов — достаточно одного smoke «через gateway можно залогиниться» (опционально).

Итого: полное покрытие user-ручек — один раз (User Service); gateway — только gateway-специфичные сценарии.

---

## Что тестируем где

| Область | User Service (`make test-user-service-local`) | API Gateway (`make test-api-gateway-local`) |
|--------|------------------------------------------------|---------------------------------------------|
| **Auth (register, login, refresh, logout)** | Полное покрытие: позитив, валидация, 401, дубликат email и т.д. | Не дублируем. Опционально: один smoke «register + login через gateway» для проверки прокси. |
| **Me, Users, Sessions, Operators, Presence** | Полное покрытие (все эндпоинты и негативы) | Не дублируем |
| **Health / Ready** | GET /health, GET /ready (user-service) | GET /health (gateway) |
| **Rate limiting** | — | Проверка ограничения частоты запросов на стороне gateway |
| **OpenAPI** | Контракт user-service (пути auth, users, sessions и т.д.) | Контракт gateway (пути video, status и т.д.) |
| **Видеопотоки (video/start, frame, stop, …)** | — | Тесты видеосессий и связанных эндпоинтов (если они живут в gateway) |

---

## Соответствие psds/api-gateway

Тесты API Gateway ориентированы на **psds/api-gateway** (каталог `../api-gateway`):

- **Порт по умолчанию:** 8080 (`config/config.yaml` или env `HTTP_PORT`/`PORT`).
- **Ручки:** GET `/health`, GET `/api/v1/status`, GET `/openapi.json`, группа `/api/v1/video/*` (start, frame, stop, active, stats, …), группа `/api/v1/clients/*`.
- **OpenAPI:** отдаётся по GET `/openapi.json` (файл `api/openapi.json`), в `paths` есть `/api/v1/video/*` и `/api/v1/clients/*`.
- **Rate limiting:** в gateway нет эндпоинта `/v1/limits/rate-limited` — тест `test_rate_limiting_on_api_gateway` при 404 по этому пути **пропускается**.

В `.env` для прогона gateway-тестов укажите `API_GATEWAY_BASE_URL=http://localhost:8080` (или порт, на котором у вас запущен gateway).

---

## Запуск

- **Только User Service** (на порту поднимается user-service):
  ```bash
  make test-user-service-local
  ```
  Запускаются все тесты из: test_health_user_service, test_auth_flow, test_validation_negative, test_me_user_service, test_users_user_service, test_sessions_user_service, test_operators_user_service.
  В `.env`: `API_GATEWAY_BASE_URL` / `USER_SERVICE_BASE_URL` указывают на user-service.

- **Только API Gateway** (на порту поднимается api-gateway):
  ```bash
  make test-api-gateway-local
  ```
  Запускаются только gateway-специфичные тесты: health, status, OpenAPI gateway, rate limiting (и при необходимости видеосессии).
  В `.env`: **`API_GATEWAY_BASE_URL` должен указывать на api-gateway** (например `http://localhost:8081`). Перед запуском тестов проверяется:
  - **Сервис недоступен** (нет ответа на GET /health) → выход с кодом **3** и сообщением «не удалось подключиться» / «проверьте, что API Gateway запущен».
  - **По URL отвечает не API Gateway** (health есть, но GET /api/v1/status не 200) → выход с кодом **4** и сообщением «укажите URL именно API Gateway».
  - Оба проверки прошли → тесты выполняются (успех/падение по реальным assertion).

- **Всё вместе** (gateway + user-service, e2e):
  ```bash
  make test-local
  ```
  Или запуск с docker-compose: `make test-with-docker`.

---

## Опционально: проверка прокси «gateway → user-service»

Если в проде запросы к user-ручкам идут через gateway, можно добавить **один** smoke-тест в набор API Gateway:

- Вызов через gateway: `POST .../auth/register` и `POST .../auth/login`, проверка 200/201 и наличие токена.
- Цель: убедиться, что gateway корректно проксирует запросы в user-service, а не проверять заново всю логику регистрации/логина (она уже покрыта в User Service).

Так ручки user-service не дублируются полным набором тестов на стороне gateway.

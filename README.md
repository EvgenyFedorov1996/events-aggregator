# Events Aggregator

Backend-сервис для агрегирования событий из внешнего Events Provider API.

Сервис получает события от внешнего провайдера, сохраняет их в PostgreSQL и предоставляет REST API для просмотра событий, получения доступных мест и регистрации/отмены билетов.

## Стек

- Python 3.9+
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- HTTPX
- APScheduler
- Pydantic
- Docker
- GitHub Actions
- Ruff
- Pytest

## Возможности

- Синхронизация событий с Events Provider API
- Хранение событий и мест в PostgreSQL
- Получение списка событий
- Получение информации о конкретном событии
- Получение доступных мест
- Регистрация билета
- Отмена билета
- Кэширование доступных мест
- Фоновая периодическая синхронизация
- Миграции базы данных через Alembic
- Автоматический запуск lint и tests в GitHub Actions

## Структура проекта

```text
events-aggregator/
├── app/
│   ├── api/
│   ├── cache/
│   ├── clients/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── workers/
│   ├── config.py
│   ├── database.py
│   └── main.py
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .github/
│   └── workflows/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md

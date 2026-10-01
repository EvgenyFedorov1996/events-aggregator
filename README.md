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
- Пагинация при получении событий от провайдера
- Хранение событий, мест и билетов в PostgreSQL
- Получение списка событий с пагинацией
- Фильтрация событий по дате
- Получение информации о конкретном событии
- Получение доступных мест
- Кэширование доступных мест
- Регистрация билета
- Отмена билета
- Проверка доступности места перед регистрацией
- Проверка срока окончания регистрации
- Фоновая периодическая синхронизация событий
- Ручной запуск синхронизации через API
- Хранение состояния последней синхронизации
- Миграции базы данных через Alembic
- Автоматический запуск Ruff и тестов в GitHub Actions

## API

Основные endpoints:

```text
GET    /api/health
GET    /api/events
GET    /api/events/{event_id}
GET    /api/events/{event_id}/seats
POST   /api/tickets
DELETE /api/tickets/{ticket_id}
POST   /api/sync/trigger

import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://events_user:events_password@localhost:5435/events",
)
os.environ.setdefault(
    "EVENTS_PROVIDER_URL",
    "https://events-provider.dev-2.python-labs.ru",
)
os.environ.setdefault(
    "EVENTS_PROVIDER_API_KEY",
    "test-api-key",
)

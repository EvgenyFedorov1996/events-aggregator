import pytest_asyncio

from app.database import engine


@pytest_asyncio.fixture(autouse=True)
async def dispose_engine():
    yield
    await engine.dispose()

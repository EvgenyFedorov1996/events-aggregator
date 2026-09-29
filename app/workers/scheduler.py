from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.clients.events_provider import EventsProviderClient
from app.database import AsyncSessionLocal
from app.services.sync import sync_events

scheduler = AsyncIOScheduler()


async def run_sync_job() -> None:
    client = EventsProviderClient()

    try:
        async with AsyncSessionLocal() as session:
            await sync_events(
                session=session,
                client=client,
            )
    finally:
        await client.close()


def start_scheduler() -> None:
    scheduler.add_job(
        run_sync_job,
        "interval",
        days=1,
        id="daily_events_sync",
        replace_existing=True,
    )
    scheduler.start()


def stop_scheduler() -> None:
    scheduler.shutdown()

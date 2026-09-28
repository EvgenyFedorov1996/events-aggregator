import asyncio
from datetime import datetime

from app.clients.events_provider import EventsProviderClient


async def main() -> None:
    client = EventsProviderClient()

    try:
        response = await client.get_events(
            datetime(2000, 1, 1),
        )
        print(response)
    finally:
        await client.close()


asyncio.run(main())
import asyncio

from app.clients.events_provider import EventsProviderClient

EVENT_ID = "0a15c376-b059-4df4-a701-6ca755109556"


async def main() -> None:
    client = EventsProviderClient()

    try:
        response = await client.get_available_seats(EVENT_ID)
        print(response)
    finally:
        await client.close()


asyncio.run(main())
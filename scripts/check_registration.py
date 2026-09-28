import asyncio

import httpx

from app.config import settings

EVENT_ID = "0a15c376-b059-4df4-a701-6ca755109556"
TICKET_ID = "82decc7f-622a-4649-b27b-725ff70d8228"


async def main() -> None:
    url = (
        f"{settings.events_provider_url}/api/events/"
        f"{EVENT_ID}/unregister/"
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            "DELETE",
            url,
            headers={
                "x-api-key": settings.events_provider_api_key,
            },
            json={
                "ticket_id": TICKET_ID,
            },
        )

        print("STATUS:", response.status_code)
        print("BODY:", response.text)


asyncio.run(main())
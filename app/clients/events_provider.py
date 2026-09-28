from datetime import datetime
from typing import Any
from uuid import UUID

import httpx

from app.config import settings


class EventsProviderClient:
    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            base_url=settings.events_provider_url,
            headers={
                "x-api-key": settings.events_provider_api_key,
            },
            timeout=30.0,
        )

    async def get_events(
        self,
        changed_at: datetime,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        params = {
            "changed_at": changed_at.date().isoformat(),
        }

        if cursor is not None:
            params["cursor"] = cursor

        response = await self.client.get(
            "/api/events/",
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_available_seats(
        self,
        event_id: UUID,
    ) -> dict[str, Any]:
        response = await self.client.get(
            f"/api/events/{event_id}/seats/",
        )
        response.raise_for_status()
        return response.json()

    async def register(
        self,
        event_id: UUID,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> dict[str, Any]:
        response = await self.client.post(
            f"/api/events/{event_id}/register/",
            json={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "seat": seat,
            },
        )
        response.raise_for_status()
        return response.json()

    async def unregister(
        self,
        event_id: UUID,
        ticket_id: str,
    ) -> dict[str, Any]:
        response = await self.client.request(
            "DELETE",
            f"/api/events/{event_id}/unregister/",
            json={
                "ticket_id": ticket_id,
            },
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self.client.aclose()
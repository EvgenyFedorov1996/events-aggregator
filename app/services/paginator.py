from datetime import datetime
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.clients.events_provider import EventsProviderClient


class EventsPaginator:
    def __init__(
        self,
        client: EventsProviderClient,
        changed_at: datetime,
    ) -> None:
        self.client = client
        self.changed_at = changed_at
        self.cursor: str | None = None
        self.finished = False

    def __aiter__(self) -> "EventsPaginator":
        return self

    async def __anext__(self) -> dict[str, Any]:
        if self.finished:
            raise StopAsyncIteration

        response = await self.client.get_events(
            changed_at=self.changed_at,
            cursor=self.cursor,
        )

        next_url = response.get("next")

        if not next_url:
            self.finished = True
        else:
            query = parse_qs(urlparse(next_url).query)
            cursor_values = query.get("cursor")

            if not cursor_values:
                self.finished = True
            else:
                self.cursor = cursor_values[0]

        return response

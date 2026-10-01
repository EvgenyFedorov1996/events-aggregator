from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.seats import SeatsCache
from app.clients.events_provider import EventsProviderClient
from app.repositories.events import EventRepository
from app.schemas.events import AvailableSeatsResponse
from app.services.exceptions import EventNotFound


async def get_available_seats(
    session: AsyncSession,
    client: EventsProviderClient,
    cache: SeatsCache,
    event_id: UUID,
) -> AvailableSeatsResponse:
    repository = EventRepository(session)

    event = await repository.get_event_by_id(event_id)

    if event is None:
        raise EventNotFound

    cache_key = str(event_id)
    cached_seats = cache.get(cache_key)

    if cached_seats is not None:
        return AvailableSeatsResponse(
            event_id=event_id,
            available_seats=cached_seats,
        )

    response = await client.get_available_seats(event_id)
    seats = response["seats"]

    cache.set(cache_key, seats)

    return AvailableSeatsResponse(
        event_id=event_id,
        available_seats=seats,
    )

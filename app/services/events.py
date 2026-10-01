from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.events import EventRepository
from app.schemas.events import (
    EventDetailResponse,
    EventListItem,
    EventListResponse,
    PlaceDetail,
)
from app.services.exceptions import EventNotFound


async def get_events(
    session: AsyncSession,
    date_from: date | None,
    page: int,
    page_size: int,
) -> EventListResponse:
    repository = EventRepository(session)

    total_count, rows = await repository.get_events(
        date_from=date_from,
        page=page,
        page_size=page_size,
    )

    events = [
        EventListItem(
            id=event.id,
            name=event.name,
            place=place.name,
            event_time=event.event_time,
            registration_deadline=event.registration_deadline,
            status=event.status,
            number_of_visitors=event.number_of_visitors,
        )
        for event, place in rows
    ]

    total_pages = (total_count + page_size - 1) // page_size

    next_page = page + 1 if page < total_pages else None
    previous_page = page - 1 if page > 1 else None

    next_url = None
    if next_page:
        next_url = _build_page_url(
            page=next_page,
            page_size=page_size,
            date_from=date_from,
        )

    previous_url = None
    if previous_page:
        previous_url = _build_page_url(
            page=previous_page,
            page_size=page_size,
            date_from=date_from,
        )

    return EventListResponse(
        count=total_count,
        next=next_url,
        previous=previous_url,
        results=events,
    )


async def get_event(
    session: AsyncSession,
    event_id: UUID,
) -> EventDetailResponse:
    repository = EventRepository(session)

    row = await repository.get_event(event_id)

    if row is None:
        raise EventNotFound

    event, place = row

    return EventDetailResponse(
        id=event.id,
        name=event.name,
        place=PlaceDetail(
            id=place.id,
            name=place.name,
            address=place.address,
            seats_pattern=place.seats_pattern,
        ),
        event_time=event.event_time,
        registration_deadline=event.registration_deadline,
        status=event.status,
        number_of_visitors=event.number_of_visitors,
    )


def _build_page_url(
    page: int,
    page_size: int,
    date_from: date | None,
) -> str:
    if date_from is None:
        return (
            f"/api/events?page={page}"
            f"&page_size={page_size}"
        )

    return (
        f"/api/events?date_from={date_from}"
        f"&page={page}&page_size={page_size}"
    )

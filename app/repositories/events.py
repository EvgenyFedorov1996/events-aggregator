from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Event, Place


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_events(
        self,
        date_from: date | None,
        page: int,
        page_size: int,
    ) -> tuple[int, list[tuple[Event, Place]]]:
        filters = []

        if date_from is not None:
            filters.append(Event.event_time >= date_from)

        count_query = select(func.count()).select_from(Event)

        if filters:
            count_query = count_query.where(*filters)

        total_count = await self.session.scalar(count_query)

        query = (
            select(Event, Place)
            .join(Place, Event.place_id == Place.id)
            .order_by(Event.event_time)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        if filters:
            query = query.where(*filters)

        result = await self.session.execute(query)

        return total_count or 0, result.all()

    async def get_event(
        self,
        event_id: UUID,
    ) -> tuple[Event, Place] | None:
        result = await self.session.execute(
            select(Event, Place)
            .join(Place, Event.place_id == Place.id)
            .where(Event.id == event_id),
        )

        return result.first()

    async def get_event_by_id(
        self,
        event_id: UUID,
    ) -> Event | None:
        return await self.session.scalar(
            select(Event).where(Event.id == event_id),
        )

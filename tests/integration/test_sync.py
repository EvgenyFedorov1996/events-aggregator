from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.database import AsyncSessionLocal
from app.models import Event, Place, SyncState
from app.services.sync import sync_events


@pytest.mark.asyncio
async def test_sync_events_saves_event_and_place():
    place_id = uuid4()
    event_id = uuid4()

    class FakeProviderClient:
        async def get_events(self, changed_at, cursor=None):
            return {
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": str(event_id),
                        "name": "Test event",
                        "place": {
                            "id": str(place_id),
                            "name": "Test place",
                            "address": "Test address",
                            "seats_pattern": "A1-100,B1-200",
                        },
                        "event_time": "2026-10-01T18:00:00+03:00",
                        "registration_deadline": (
                            "2026-09-30T18:00:00+03:00"
                        ),
                        "status": "published",
                        "number_of_visitors": 10,
                        "changed_at": "2026-09-27T21:00:00+03:00",
                    },
                ],
            }

    async with AsyncSessionLocal() as session:
        await sync_events(
            session=session,
            client=FakeProviderClient(),
        )

        place = await session.scalar(
            select(Place).where(Place.id == place_id),
        )
        event = await session.scalar(
            select(Event).where(Event.id == event_id),
        )

        assert place is not None
        assert place.name == "Test place"
        assert place.seats_pattern == "A1-100,B1-200"

        assert event is not None
        assert event.name == "Test event"
        assert event.place_id == place_id
        assert event.number_of_visitors == 10

        await session.delete(event)
        await session.delete(place)
        await session.commit()


@pytest.mark.asyncio
async def test_sync_events_updates_existing_event():
    place_id = uuid4()
    event_id = uuid4()

    class FakeProviderClient:
        def __init__(self):
            self.name = "Initial event"
            self.visitors = 10

        async def get_events(self, changed_at, cursor=None):
            return {
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": str(event_id),
                        "name": self.name,
                        "place": {
                            "id": str(place_id),
                            "name": "Test place",
                            "address": "Test address",
                            "seats_pattern": "A1-100,B1-200",
                        },
                        "event_time": "2026-10-01T18:00:00+03:00",
                        "registration_deadline": (
                            "2026-09-30T18:00:00+03:00"
                        ),
                        "status": "published",
                        "number_of_visitors": self.visitors,
                        "changed_at": "2026-09-27T21:00:00+03:00",
                    },
                ],
            }

    client = FakeProviderClient()

    async with AsyncSessionLocal() as session:
        await sync_events(
            session=session,
            client=client,
        )

        client.name = "Updated event"
        client.visitors = 25

        await sync_events(
            session=session,
            client=client,
        )

        events = (
            await session.scalars(
                select(Event).where(Event.id == event_id),
            )
        ).all()

        assert len(events) == 1
        assert events[0].name == "Updated event"
        assert events[0].number_of_visitors == 25

        await session.delete(events[0])

        place = await session.scalar(
            select(Place).where(Place.id == place_id),
        )
        assert place is not None

        await session.delete(place)
        await session.commit()


@pytest.mark.asyncio
async def test_sync_events_saves_last_changed_at():
    from datetime import datetime

    place_id = uuid4()
    event_id = uuid4()

    provider_changed_at = "2026-09-27T22:00:00+03:00"

    class FakeProviderClient:
        async def get_events(self, changed_at, cursor=None):
            return {
                "next": None,
                "previous": None,
                "results": [
                    {
                        "id": str(event_id),
                        "name": "Test event",
                        "place": {
                            "id": str(place_id),
                            "name": "Test place",
                            "address": "Test address",
                            "seats_pattern": "A1-100",
                        },
                        "event_time": "2026-10-01T18:00:00+03:00",
                        "registration_deadline": (
                            "2026-09-30T18:00:00+03:00"
                        ),
                        "status": "published",
                        "number_of_visitors": 10,
                        "changed_at": provider_changed_at,
                    },
                ],
            }

    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(SyncState).where(SyncState.id == 1),
        )
        await session.commit()

        await sync_events(
            session=session,
            client=FakeProviderClient(),
        )

        sync_state = await session.scalar(
            select(SyncState).where(SyncState.id == 1),
        )

        assert sync_state is not None
        assert sync_state.last_changed_at == datetime.fromisoformat(
            provider_changed_at,
        )
        assert sync_state.last_sync_time is not None
        assert sync_state.sync_status == "success"

        event = await session.scalar(
            select(Event).where(Event.id == event_id),
        )
        place = await session.scalar(
            select(Place).where(Place.id == place_id),
        )

        await session.delete(event)
        await session.delete(place)
        await session.delete(sync_state)
        await session.commit()

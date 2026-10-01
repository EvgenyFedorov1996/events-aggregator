import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.events_provider import EventsProviderClient
from app.models import Event, Place, SyncState
from app.models.enums import EventStatus, SyncStatus
from app.services.paginator import EventsPaginator

logger = logging.getLogger(__name__)


async def _get_or_create_sync_state(
    session: AsyncSession,
) -> SyncState:
    sync_state = await session.scalar(
        select(SyncState).where(SyncState.id == 1),
    )

    if sync_state is None:
        sync_state = SyncState(
            id=1,
            sync_status=SyncStatus.NEVER,
        )
        session.add(sync_state)
        await session.flush()

    return sync_state


async def sync_events(
    session: AsyncSession,
    client: EventsProviderClient,
) -> None:
    """Synchronize events from the Events Provider."""
    sync_state = await _get_or_create_sync_state(session)

    try:
        changed_at = sync_state.last_changed_at

        if changed_at is None:
            changed_at = datetime(
                2000,
                1,
                1,
                tzinfo=timezone.utc,
            )

        latest_changed_at = changed_at

        paginator = EventsPaginator(
            client=client,
            changed_at=changed_at,
        )

        async for response in paginator:
            for event_data in response["results"]:
                place_data = event_data["place"]

                place_id = UUID(place_data["id"])

                place = await session.scalar(
                    select(Place).where(Place.id == place_id),
                )

                if place is None:
                    place = Place(
                        id=place_id,
                        name=place_data["name"],
                        address=place_data["address"],
                        seats_pattern=place_data["seats_pattern"],
                    )
                    session.add(place)
                else:
                    place.name = place_data["name"]
                    place.address = place_data["address"]
                    place.seats_pattern = place_data["seats_pattern"]

                event_id = UUID(event_data["id"])

                event = await session.scalar(
                    select(Event).where(Event.id == event_id),
                )

                event_changed_at = datetime.fromisoformat(
                    event_data["changed_at"],
                )

                event_status = EventStatus(event_data["status"])

                if event is None:
                    event = Event(
                        id=event_id,
                        name=event_data["name"],
                        place_id=place_id,
                        event_time=datetime.fromisoformat(
                            event_data["event_time"],
                        ),
                        registration_deadline=datetime.fromisoformat(
                            event_data["registration_deadline"],
                        ),
                        status=event_status,
                        number_of_visitors=event_data["number_of_visitors"],
                        changed_at=event_changed_at,
                    )
                    session.add(event)
                else:
                    event.name = event_data["name"]
                    event.place_id = place_id
                    event.event_time = datetime.fromisoformat(
                        event_data["event_time"],
                    )
                    event.registration_deadline = datetime.fromisoformat(
                        event_data["registration_deadline"],
                    )
                    event.status = event_status
                    event.number_of_visitors = event_data["number_of_visitors"]
                    event.changed_at = event_changed_at

                if event_changed_at > latest_changed_at:
                    latest_changed_at = event_changed_at

        sync_state.last_changed_at = latest_changed_at
        sync_state.last_sync_time = datetime.now(timezone.utc)
        sync_state.sync_status = SyncStatus.SUCCESS

        await session.commit()

    except Exception:
        await session.rollback()

        sync_state.sync_status = SyncStatus.FAILED
        await session.commit()

        logger.exception("Events synchronization failed")

        raise

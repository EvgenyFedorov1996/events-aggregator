from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.events_provider import EventsProviderClient
from app.models import Event, Ticket
from app.services.exceptions import (
    EventNotFound,
    RegistrationClosed,
    SeatNotAvailable,
    TicketNotFound,
)


async def create_ticket(
    session: AsyncSession,
    client: EventsProviderClient,
    event_id: UUID,
    first_name: str,
    last_name: str,
    email: str,
    seat: str,
) -> Ticket:
    event = await session.scalar(
        select(Event).where(Event.id == event_id),
    )

    if event is None:
        raise EventNotFound

    if datetime.now(timezone.utc) >= event.registration_deadline:
        raise RegistrationClosed

    seats_response = await client.get_available_seats(event_id)
    available_seats = seats_response["seats"]

    if seat not in available_seats:
        raise SeatNotAvailable

    provider_response = await client.register(
        event_id=event_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        seat=seat,
    )

    provider_ticket_id = UUID(provider_response["ticket_id"])

    ticket = Ticket(
        id=uuid4(),
        provider_ticket_id=provider_ticket_id,
        event_id=event_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        seat=seat,
    )

    session.add(ticket)
    await session.commit()
    await session.refresh(ticket)

    return ticket


async def delete_ticket(
    session: AsyncSession,
    client: EventsProviderClient,
    ticket_id: UUID,
) -> None:
    ticket = await session.scalar(
        select(Ticket).where(Ticket.id == ticket_id),
    )

    if ticket is None:
        raise TicketNotFound

    await client.unregister(
        event_id=ticket.event_id,
        ticket_id=str(ticket.provider_ticket_id),
    )

    await session.delete(ticket)
    await session.commit()

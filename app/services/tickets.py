from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.events_provider import EventsProviderClient
from app.models import Event, Ticket


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
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    if datetime.now(timezone.utc) >= event.registration_deadline:
        raise HTTPException(
            status_code=400,
            detail="Registration is closed",
        )

    seats_response = await client.get_available_seats(event_id)
    available_seats = seats_response["seats"]

    if seat not in available_seats:
        raise HTTPException(
            status_code=400,
            detail="Seat is not available",
        )

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
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    await client.unregister(
        event_id=ticket.event_id,
        ticket_id=str(ticket.provider_ticket_id),
    )

    await session.delete(ticket)
    await session.commit()

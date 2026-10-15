from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.events_provider import EventsProviderClient
from app.models import (
    Event,
    OutboxEvent,
    Ticket,
    TicketIdempotencyKey,
)
from app.services.exceptions import (
    EventNotFound,
    IdempotencyConflict,
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
    idempotency_key: str | None = None,
) -> Ticket:
    request_payload = {
        "event_id": str(event_id),
        "first_name": first_name,
        "last_name": last_name,
        "email": str(email),
        "seat": seat,
    }

    if idempotency_key is not None:
        # Serialize requests using the same key in PostgreSQL.
        # The lock is held until this transaction commits or rolls back.
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
            {"key": idempotency_key},
        )

        existing_key = await session.scalar(
            select(TicketIdempotencyKey).where(
                TicketIdempotencyKey.key == idempotency_key
            )
        )

        if existing_key is not None:
            if existing_key.request_payload != request_payload:
                await session.rollback()
                raise IdempotencyConflict

            existing_ticket = await session.scalar(
                select(Ticket).where(Ticket.id == existing_key.ticket_id)
            )

            if existing_ticket is None:
                await session.rollback()
                raise IdempotencyConflict

            # Release the transaction-level advisory lock.
            await session.commit()
            return existing_ticket

    event = await session.scalar(
        select(Event).where(Event.id == event_id),
    )

    if event is None:
        await session.rollback()
        raise EventNotFound

    if datetime.now(timezone.utc) >= event.registration_deadline:
        await session.rollback()
        raise RegistrationClosed

    seats_response = await client.get_available_seats(event_id)
    available_seats = seats_response["seats"]

    if seat not in available_seats:
        await session.rollback()
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

    message = (
        f"Ticket registered: {first_name} {last_name}; "
        f"event {event_id}; seat {seat}; "
        f"ticket {ticket.id}."
    )

    outbox_event = OutboxEvent(
        id=uuid4(),
        event_type="ticket.created",
        payload={
            "ticket_id": str(ticket.id),
            "message": message,
            "reference_id": str(ticket.id),
            "idempotency_key": f"ticket:{ticket.id}",
        },
        status="pending",
    )

    session.add(ticket)
    session.add(outbox_event)

    if idempotency_key is not None:
        session.add(
            TicketIdempotencyKey(
                key=idempotency_key,
                request_payload=request_payload,
                ticket_id=ticket.id,
            )
        )

    try:
        await session.commit()
        await session.refresh(ticket)
    except Exception:
        await session.rollback()
        raise

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

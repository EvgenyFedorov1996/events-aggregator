from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.exceptions import (
    EventNotFound,
    RegistrationClosed,
    SeatNotAvailable,
    TicketNotFound,
)
from app.services.tickets import create_ticket, delete_ticket


@pytest.mark.asyncio
async def test_create_ticket_success():
    event_id = uuid4()

    event = type(
        "Event",
        (),
        {
            "id": event_id,
            "status": "published",
            "registration_deadline": datetime.now(timezone.utc) + timedelta(hours=1),
        },
    )()

    session = MagicMock()
    session.rollback = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.scalar = AsyncMock(return_value=event)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    client = AsyncMock()
    client.get_available_seats.return_value = {
        "seats": ["A1", "A2", "B1"],
    }
    client.register.return_value = {
        "ticket_id": str(uuid4()),
    }

    ticket = await create_ticket(
        session=session,
        client=client,
        event_id=event_id,
        first_name="Test",
        last_name="User",
        email="test@example.com",
        seat="A1",
    )

    assert ticket.event_id == event_id
    assert ticket.first_name == "Test"
    assert ticket.last_name == "User"
    assert ticket.email == "test@example.com"
    assert ticket.seat == "A1"

    client.get_available_seats.assert_awaited_once_with(event_id)
    client.register.assert_awaited_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_ticket_event_not_found():
    session = MagicMock()
    session.rollback = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    client = AsyncMock()

    with pytest.raises(EventNotFound):
        await create_ticket(
            session=session,
            client=client,
            event_id=uuid4(),
            first_name="Test",
            last_name="User",
            email="test@example.com",
            seat="A1",
        )

    client.get_available_seats.assert_not_awaited()
    client.register.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_ticket_registration_closed():
    event_id = uuid4()

    event = type(
        "Event",
        (),
        {
            "id": event_id,
            "status": "published",
            "registration_deadline": datetime.now(timezone.utc) - timedelta(hours=1),
        },
    )()

    session = MagicMock()
    session.rollback = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.scalar = AsyncMock(return_value=event)

    client = AsyncMock()

    with pytest.raises(RegistrationClosed):
        await create_ticket(
            session=session,
            client=client,
            event_id=event_id,
            first_name="Test",
            last_name="User",
            email="test@example.com",
            seat="A1",
        )

    client.get_available_seats.assert_not_awaited()
    client.register.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_ticket_seat_not_available():
    event_id = uuid4()

    event = type(
        "Event",
        (),
        {
            "id": event_id,
            "status": "published",
            "registration_deadline": datetime.now(timezone.utc) + timedelta(hours=1),
        },
    )()

    session = MagicMock()
    session.rollback = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.scalar = AsyncMock(return_value=event)

    client = AsyncMock()
    client.get_available_seats.return_value = {
        "seats": ["A1", "A2", "B1"],
    }

    with pytest.raises(SeatNotAvailable):
        await create_ticket(
            session=session,
            client=client,
            event_id=event_id,
            first_name="Test",
            last_name="User",
            email="test@example.com",
            seat="C1",
        )

    client.register.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_ticket_success():
    ticket_id = uuid4()
    event_id = uuid4()
    provider_ticket_id = uuid4()

    ticket = type(
        "Ticket",
        (),
        {
            "id": ticket_id,
            "event_id": event_id,
            "provider_ticket_id": provider_ticket_id,
        },
    )()

    session = MagicMock()
    session.rollback = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.scalar = AsyncMock(return_value=ticket)
    session.delete = AsyncMock()
    session.commit = AsyncMock()

    client = AsyncMock()

    await delete_ticket(
        session=session,
        client=client,
        ticket_id=ticket_id,
    )

    client.unregister.assert_awaited_once_with(
        event_id=event_id,
        ticket_id=str(provider_ticket_id),
    )

    session.delete.assert_awaited_once_with(ticket)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_ticket_not_found():
    session = MagicMock()
    session.rollback = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    client = AsyncMock()

    ticket_id = uuid4()

    with pytest.raises(TicketNotFound):
        await delete_ticket(
            session=session,
            client=client,
            ticket_id=ticket_id,
        )

    client.unregister.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_ticket_idempotent_replay_returns_existing_ticket():

    event_id = uuid4()
    ticket_id = uuid4()
    key = "registration-123"

    request_payload = {
        "event_id": str(event_id),
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "seat": "A1",
    }

    existing_key = MagicMock()
    existing_key.request_payload = request_payload
    existing_key.ticket_id = ticket_id

    existing_ticket = MagicMock()
    existing_ticket.id = ticket_id

    session = MagicMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock(
        side_effect=[existing_key, existing_ticket],
    )
    session.commit = AsyncMock()
    session.rollback = AsyncMock()

    client = AsyncMock()

    result = await create_ticket(
        session=session,
        client=client,
        event_id=event_id,
        first_name="Test",
        last_name="User",
        email="test@example.com",
        seat="A1",
        idempotency_key=key,
    )

    assert result is existing_ticket
    client.get_available_seats.assert_not_awaited()
    client.register.assert_not_awaited()
    session.add.assert_not_called()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_ticket_idempotency_key_conflict():
    from app.services.exceptions import IdempotencyConflict

    event_id = uuid4()
    existing_key = MagicMock()
    existing_key.request_payload = {
        "event_id": str(event_id),
        "first_name": "Different",
        "last_name": "User",
        "email": "test@example.com",
        "seat": "A1",
    }

    session = MagicMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock(return_value=existing_key)
    session.rollback = AsyncMock()

    client = AsyncMock()

    with pytest.raises(IdempotencyConflict):
        await create_ticket(
            session=session,
            client=client,
            event_id=event_id,
            first_name="Test",
            last_name="User",
            email="test@example.com",
            seat="A1",
            idempotency_key="registration-123",
        )

    session.rollback.assert_awaited_once()
    client.get_available_seats.assert_not_awaited()
    client.register.assert_not_awaited()
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_create_ticket_with_idempotency_adds_outbox_event():
    from app.models import OutboxEvent, TicketIdempotencyKey

    event_id = uuid4()
    event = type(
        "Event",
        (),
        {
            "id": event_id,
            "status": "published",
            "registration_deadline": datetime.now(timezone.utc)
            + timedelta(hours=1),
        },
    )()

    session = MagicMock()
    session.execute = AsyncMock()
    session.rollback = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.scalar = AsyncMock(side_effect=[None, event])

    client = AsyncMock()
    client.get_available_seats.return_value = {"seats": ["A1"]}
    client.register.return_value = {"ticket_id": str(uuid4())}

    ticket = await create_ticket(
        session=session,
        client=client,
        event_id=event_id,
        first_name="Test",
        last_name="User",
        email="test@example.com",
        seat="A1",
        idempotency_key="registration-456",
    )

    added_objects = [call.args[0] for call in session.add.call_args_list]

    assert any(isinstance(obj, OutboxEvent) for obj in added_objects)
    assert any(
        isinstance(obj, TicketIdempotencyKey) for obj in added_objects
    )
    assert any(obj is ticket for obj in added_objects)
    assert session.commit.await_count == 1
    client.register.assert_awaited_once()

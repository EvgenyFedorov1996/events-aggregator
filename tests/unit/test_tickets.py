from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

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
            "registration_deadline": datetime.now(timezone.utc)
            + timedelta(hours=1),
        },
    )()

    session = MagicMock()
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
    session.scalar = AsyncMock(return_value=None)

    client = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await create_ticket(
            session=session,
            client=client,
            event_id=uuid4(),
            first_name="Test",
            last_name="User",
            email="test@example.com",
            seat="A1",
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Event not found"

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
            "registration_deadline": datetime.now(timezone.utc)
            - timedelta(hours=1),
        },
    )()

    session = MagicMock()
    session.scalar = AsyncMock(return_value=event)

    client = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        await create_ticket(
            session=session,
            client=client,
            event_id=event_id,
            first_name="Test",
            last_name="User",
            email="test@example.com",
            seat="A1",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Registration is closed"

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
            "registration_deadline": datetime.now(timezone.utc)
            + timedelta(hours=1),
        },
    )()

    session = MagicMock()
    session.scalar = AsyncMock(return_value=event)

    client = AsyncMock()
    client.get_available_seats.return_value = {
        "seats": ["A1", "A2", "B1"],
    }

    with pytest.raises(HTTPException) as exc_info:
        await create_ticket(
            session=session,
            client=client,
            event_id=event_id,
            first_name="Test",
            last_name="User",
            email="test@example.com",
            seat="C1",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Seat is not available"

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
    session.scalar = AsyncMock(return_value=None)

    client = AsyncMock()

    ticket_id = uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await delete_ticket(
            session=session,
            client=client,
            ticket_id=ticket_id,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Ticket not found"

    client.unregister.assert_not_awaited()

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.workers.outbox import process_outbox_batch


@pytest.mark.asyncio
async def test_process_outbox_batch_marks_event_sent(monkeypatch):
    event = MagicMock()
    event.id = "event-1"
    event.status = "pending"
    event.sent_at = None
    event.payload = {
        "message": "Ticket registered",
        "reference_id": "ticket-123",
        "idempotency_key": "ticket:ticket-123",
    }

    session = MagicMock()
    session.scalars = AsyncMock(return_value=[event])
    session.commit = AsyncMock()

    client = MagicMock()
    client.send_notification = AsyncMock()

    monkeypatch.setattr(
        "app.workers.outbox.settings.outbox_batch_size",
        100,
    )

    sent_count = await process_outbox_batch(session, client)

    assert sent_count == 1
    assert event.status == "sent"
    assert event.sent_at is not None
    session.commit.assert_awaited_once()
    client.send_notification.assert_awaited_once_with(
        message="Ticket registered",
        reference_id="ticket-123",
        idempotency_key="ticket:ticket-123",
    )


@pytest.mark.asyncio
async def test_process_outbox_batch_keeps_failed_event_pending(
    monkeypatch,
):
    event = MagicMock()
    event.id = "event-2"
    event.status = "pending"
    event.sent_at = None
    event.payload = {
        "message": "Ticket registered",
        "reference_id": "ticket-456",
        "idempotency_key": "ticket:ticket-456",
    }

    session = MagicMock()
    session.scalars = AsyncMock(return_value=[event])
    session.commit = AsyncMock()

    client = MagicMock()
    client.send_notification = AsyncMock(
        side_effect=RuntimeError("Capashino unavailable")
    )

    monkeypatch.setattr(
        "app.workers.outbox.settings.outbox_batch_size",
        100,
    )

    sent_count = await process_outbox_batch(session, client)

    assert sent_count == 0
    assert event.status == "pending"
    assert event.sent_at is None
    session.commit.assert_awaited_once()

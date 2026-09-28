from unittest.mock import AsyncMock

import pytest

from app.models import SyncState
from app.services.sync import sync_events


@pytest.mark.asyncio
async def test_sync_events_requests_events_from_provider():
    session = AsyncMock()
    session.add = lambda _: None
    client = AsyncMock()

    session.scalar.return_value = None

    client.get_events.return_value = {
        "results": [
            {
                "id": "00000000-0000-0000-0000-000000000004",
                "name": "Event 1",
                "place": {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "name": "Place 1",
                    "address": "Address 1",
                    "seats_pattern": "A1-100",
                },
                "event_time": "2026-10-01T18:00:00+03:00",
                "registration_deadline": "2026-09-30T18:00:00+03:00",
                "status": "published",
                "number_of_visitors": 10,
                "changed_at": "2026-09-27T21:00:00+03:00",
            },
            {
                "id": "00000000-0000-0000-0000-000000000002",
                "name": "Event 2",
                "place": {
                    "id": "00000000-0000-0000-0000-000000000003",
                    "name": "Place 2",
                    "address": "Address 2",
                    "seats_pattern": "B1-200",
                },
                "event_time": "2026-10-02T18:00:00+03:00",
                "registration_deadline": "2026-10-01T18:00:00+03:00",
                "status": "published",
                "number_of_visitors": 20,
                "changed_at": "2026-09-27T22:00:00+03:00",
            },
        ],
        "next": None,
    }

    await sync_events(
        session=session,
        client=client,
    )

    client.get_events.assert_awaited_once()

    changed_at = client.get_events.await_args.kwargs["changed_at"]

    assert changed_at.year == 2000
    assert changed_at.month == 1
    assert changed_at.day == 1


@pytest.mark.asyncio
async def test_sync_events_handles_pagination():
    session = AsyncMock()
    session.add = lambda _: None
    client = AsyncMock()

    session.scalar.return_value = None

    first_page = {
        "results": [
            {
                "id": "00000000-0000-0000-0000-000000000004",
                "name": "Event 1",
                "place": {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "name": "Place 1",
                    "address": "Address 1",
                    "seats_pattern": "A1-100",
                },
                "event_time": "2026-10-01T18:00:00+03:00",
                "registration_deadline": "2026-09-30T18:00:00+03:00",
                "status": "published",
                "number_of_visitors": 10,
                "changed_at": "2026-09-27T21:00:00+03:00",
            },
        ],
        "next": (
            "http://events-provider.dev-2.python-labs.ru/"
            "api/events/?changed_at=2000-01-01&cursor=abc123"
        ),
    }

    second_page = {
        "results": [
            {
                "id": "00000000-0000-0000-0000-000000000005",
                "name": "Event 2",
                "place": {
                    "id": "00000000-0000-0000-0000-000000000002",
                    "name": "Place 2",
                    "address": "Address 2",
                    "seats_pattern": "B1-200",
                },
                "event_time": "2026-10-02T18:00:00+03:00",
                "registration_deadline": "2026-10-01T18:00:00+03:00",
                "status": "published",
                "number_of_visitors": 20,
                "changed_at": "2026-09-27T22:00:00+03:00",
            },
        ],
        "next": None,
    }

    client.get_events.side_effect = [
        first_page,
        second_page,
    ]

    await sync_events(
        session=session,
        client=client,
    )

    assert client.get_events.await_count == 2

    first_call = client.get_events.await_args_list[0]
    second_call = client.get_events.await_args_list[1]

    assert first_call.kwargs["cursor"] is None
    assert second_call.kwargs["cursor"] == "abc123"


@pytest.mark.asyncio
async def test_sync_events_marks_status_as_failed_on_error():
    session = AsyncMock()
    session.add = lambda _: None
    client = AsyncMock()

    sync_state = SyncState(
        id=1,
        sync_status="never",
    )

    session.scalar.return_value = sync_state

    client.get_events.side_effect = RuntimeError("Provider is unavailable")

    with pytest.raises(RuntimeError, match="Provider is unavailable"):
        await sync_events(
            session=session,
            client=client,
        )

    assert sync_state.sync_status == "failed"

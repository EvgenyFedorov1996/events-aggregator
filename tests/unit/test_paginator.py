from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.services.paginator import EventsPaginator


@pytest.mark.asyncio
async def test_paginator_single_page():
    changed_at = datetime(
        2026,
        9,
        30,
        tzinfo=timezone.utc,
    )

    client = AsyncMock()
    client.get_events.return_value = {
        "results": [{"id": "event-1"}],
        "next": None,
    }

    paginator = EventsPaginator(
        client=client,
        changed_at=changed_at,
    )

    pages = []

    async for page in paginator:
        pages.append(page)

    assert pages == [
        {
            "results": [{"id": "event-1"}],
            "next": None,
        },
    ]

    client.get_events.assert_awaited_once_with(
        changed_at=changed_at,
        cursor=None,
    )


@pytest.mark.asyncio
async def test_paginator_multiple_pages():
    changed_at = datetime(
        2026,
        9,
        30,
        tzinfo=timezone.utc,
    )

    client = AsyncMock()
    client.get_events.side_effect = [
        {
            "results": [{"id": "event-1"}],
            "next": (
                "https://provider.test/api/events/"
                "?changed_at=2026-09-30&cursor=abc123"
            ),
        },
        {
            "results": [{"id": "event-2"}],
            "next": None,
        },
    ]

    paginator = EventsPaginator(
        client=client,
        changed_at=changed_at,
    )

    pages = []

    async for page in paginator:
        pages.append(page)

    assert len(pages) == 2
    assert pages[0]["results"] == [{"id": "event-1"}]
    assert pages[1]["results"] == [{"id": "event-2"}]

    assert client.get_events.await_args_list[0].kwargs == {
        "changed_at": changed_at,
        "cursor": None,
    }

    assert client.get_events.await_args_list[1].kwargs == {
        "changed_at": changed_at,
        "cursor": "abc123",
    }


@pytest.mark.asyncio
async def test_paginator_stops_when_next_has_no_cursor():
    changed_at = datetime(
        2026,
        9,
        30,
        tzinfo=timezone.utc,
    )

    client = AsyncMock()
    client.get_events.return_value = {
        "results": [{"id": "event-1"}],
        "next": "https://provider.test/api/events/?changed_at=2026-09-30",
    }

    paginator = EventsPaginator(
        client=client,
        changed_at=changed_at,
    )

    pages = []

    async for page in paginator:
        pages.append(page)

    assert len(pages) == 1
    client.get_events.assert_awaited_once()


@pytest.mark.asyncio
async def test_paginator_stops_when_next_is_none():
    changed_at = datetime(
        2026,
        9,
        30,
        tzinfo=timezone.utc,
    )

    client = AsyncMock()
    client.get_events.return_value = {
        "results": [],
        "next": None,
    }

    paginator = EventsPaginator(
        client=client,
        changed_at=changed_at,
    )

    pages = []

    async for page in paginator:
        pages.append(page)

    assert len(pages) == 1
    assert pages[0]["results"] == []

    client.get_events.assert_awaited_once_with(
        changed_at=changed_at,
        cursor=None,
    )

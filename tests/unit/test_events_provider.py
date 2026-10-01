import json
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import pytest

from app.clients.events_provider import EventsProviderClient


@pytest.mark.asyncio
async def test_get_events_sends_api_key_and_query_params(monkeypatch):
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        return httpx.Response(
            200,
            json={
                "results": [],
                "next": None,
                "previous": None,
            },
        )

    client = EventsProviderClient()
    await client.client.aclose()

    client.client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://example.com",
        headers={"x-api-key": "test-api-key"},
    )

    try:
        changed_at = datetime(
            2026,
            9,
            30,
            12,
            0,
            tzinfo=timezone.utc,
        )

        result = await client.get_events(
            changed_at=changed_at,
            cursor="cursor-123",
        )

        assert result["results"] == []

        request = requests[0]

        assert request.url.path == "/api/events/"
        assert request.url.params["changed_at"] == "2026-09-30"
        assert request.url.params["cursor"] == "cursor-123"
        assert request.headers["x-api-key"] == "test-api-key"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_events_without_cursor_does_not_send_cursor():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/events/"
        assert request.url.params["changed_at"] == "2026-09-30"
        assert "cursor" not in request.url.params

        return httpx.Response(
            200,
            json={
                "results": [],
                "next": None,
                "previous": None,
            },
        )

    client = EventsProviderClient()
    await client.client.aclose()

    client.client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://example.com",
        headers={"x-api-key": "test-api-key"},
    )

    try:
        await client.get_events(
            changed_at=datetime(
                2026,
                9,
                30,
                tzinfo=timezone.utc,
            ),
        )
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_events_raises_for_http_error():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500,
            json={"detail": "Provider error"},
        )

    client = EventsProviderClient()
    await client.client.aclose()

    client.client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://example.com",
        headers={"x-api-key": "test-api-key"},
    )

    try:
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_events(
                changed_at=datetime(
                    2026,
                    9,
                    30,
                    tzinfo=timezone.utc,
                ),
            )
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_get_available_seats():
    event_id = uuid4()

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/api/events/{event_id}/seats/"
        assert request.headers["x-api-key"] == "test-api-key"

        return httpx.Response(
            200,
            json={"seats": ["A1", "A2"]},
        )

    client = EventsProviderClient()
    await client.client.aclose()

    client.client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://example.com",
        headers={"x-api-key": "test-api-key"},
    )

    try:
        result = await client.get_available_seats(event_id)

        assert result == {"seats": ["A1", "A2"]}
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_register():
    event_id = uuid4()

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == f"/api/events/{event_id}/register/"
        assert request.headers["x-api-key"] == "test-api-key"
        assert json.loads(request.content) == {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "seat": "A1",
        }

        return httpx.Response(
            200,
            json={"ticket_id": str(uuid4())},
        )

    client = EventsProviderClient()
    await client.client.aclose()

    client.client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://example.com",
        headers={"x-api-key": "test-api-key"},
    )

    try:
        result = await client.register(
            event_id=event_id,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            seat="A1",
        )

        assert "ticket_id" in result
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_unregister():
    event_id = uuid4()

    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == f"/api/events/{event_id}/unregister/"
        assert request.headers["x-api-key"] == "test-api-key"
        assert json.loads(request.content) == {
            "ticket_id": "ticket-123",
        }

        return httpx.Response(
            200,
            json={"success": True},
        )

    client = EventsProviderClient()
    await client.client.aclose()

    client.client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://example.com",
        headers={"x-api-key": "test-api-key"},
    )

    try:
        result = await client.unregister(
            event_id=event_id,
            ticket_id="ticket-123",
        )

        assert result == {"success": True}
    finally:
        await client.close()

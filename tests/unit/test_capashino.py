import httpx
import pytest

from app.clients.capashino import CapashinoClient


@pytest.mark.asyncio
async def test_send_notification(monkeypatch):
    client = CapashinoClient()
    captured = {}

    async def mock_post(self, url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs["headers"]
        captured["json"] = kwargs["json"]
        return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    monkeypatch.setattr(client, "api_key", "test-api-key")
    monkeypatch.setattr(client, "base_url", "http://capashino.test")

    await client.send_notification(
        message="Ticket registered",
        reference_id="ticket-123",
        idempotency_key="ticket:ticket-123",
    )

    assert captured["url"] == ("http://capashino.test/api/notifications")
    assert captured["headers"]["X-API-Key"] == "test-api-key"
    assert captured["json"] == {
        "message": "Ticket registered",
        "reference_id": "ticket-123",
        "idempotency_key": "ticket:ticket-123",
    }


@pytest.mark.asyncio
async def test_send_notification_raises_for_http_error(monkeypatch):
    client = CapashinoClient()

    async def mock_post(self, url, **kwargs):
        request = httpx.Request("POST", url)
        return httpx.Response(500, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    with pytest.raises(httpx.HTTPStatusError):
        await client.send_notification(
            message="Ticket registered",
            reference_id="ticket-123",
            idempotency_key="ticket:ticket-123",
        )

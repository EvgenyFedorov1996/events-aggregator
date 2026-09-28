from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_trigger_sync():
    with patch(
        "app.main.sync_events",
        new_callable=AsyncMock,
    ) as mock_sync:
        response = client.post("/api/sync/trigger")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    mock_sync.assert_awaited_once()
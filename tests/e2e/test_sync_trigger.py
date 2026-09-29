from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_trigger_sync():
    with patch(
        "app.main.run_sync_job",
    ) as mock_sync:
        response = client.post("/api/sync/trigger")

    assert response.status_code == 202
    assert response.json() == {"status": "accepted"}
    mock_sync.assert_called_once()

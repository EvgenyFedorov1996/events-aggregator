from unittest.mock import AsyncMock, patch

import pytest

from app.workers.scheduler import run_sync_job


@pytest.mark.asyncio
async def test_run_sync_job_calls_sync():
    with patch(
        "app.workers.scheduler.sync_events",
        new_callable=AsyncMock,
    ) as mock_sync:
        await run_sync_job()

    mock_sync.assert_awaited_once()
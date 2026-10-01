from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.services.seats import get_available_seats


@pytest.mark.asyncio
async def test_get_available_seats_uses_cache():
    event_id = uuid4()

    session = AsyncMock()
    session.scalar.return_value = object()

    provider_response = {
        "seats": ["A1", "A2", "B1"],
    }

    mock_cache = MagicMock()
    mock_cache.get.side_effect = [
        None,
        ["A1", "A2", "B1"],
    ]

    mock_client = AsyncMock()
    mock_client.get_available_seats.return_value = provider_response

    first_response = await get_available_seats(
        event_id=event_id,
        session=session,
        client=mock_client,
        cache=mock_cache,
    )

    second_response = await get_available_seats(
        event_id=event_id,
        session=session,
        client=mock_client,
        cache=mock_cache,
    )

    assert first_response.event_id == event_id
    assert first_response.available_seats == ["A1", "A2", "B1"]

    assert second_response.event_id == event_id
    assert second_response.available_seats == ["A1", "A2", "B1"]

    mock_client.get_available_seats.assert_awaited_once()

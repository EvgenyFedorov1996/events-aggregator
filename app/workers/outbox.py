import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.clients.capashino import CapashinoClient
from app.config import settings
from app.database import AsyncSessionLocal
from app.models import OutboxEvent

logger = logging.getLogger(__name__)


async def process_outbox_batch(
    session: AsyncSession,
    client: CapashinoClient,
) -> int:
    result = await session.scalars(
        select(OutboxEvent)
        .where(OutboxEvent.status == "pending")
        .order_by(OutboxEvent.created_at)
        .limit(settings.outbox_batch_size)
        .with_for_update(skip_locked=True)
    )
    events = list(result)

    if not events:
        return 0

    sent_count = 0

    for event in events:
        try:
            payload = event.payload

            await client.send_notification(
                message=payload["message"],
                reference_id=payload["reference_id"],
                idempotency_key=payload["idempotency_key"],
            )

            event.status = "sent"
            event.sent_at = datetime.now(timezone.utc)
            sent_count += 1

        except Exception:
            logger.exception(
                "Failed to send outbox event %s",
                event.id,
            )

    await session.commit()
    return sent_count


async def outbox_worker_loop(
    session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal,
) -> None:
    client = CapashinoClient()

    while True:
        try:
            async with session_factory() as session:
                await process_outbox_batch(session, client)
        except Exception:
            logger.exception("Outbox worker iteration failed")

        await asyncio.sleep(settings.outbox_poll_interval_seconds)

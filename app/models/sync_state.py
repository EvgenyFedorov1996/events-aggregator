from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import SyncStatus


class SyncState(Base):
    __tablename__ = "sync_state"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )
    last_sync_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_changed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    sync_status: Mapped[SyncStatus] = mapped_column(
        String(50),
        nullable=False,
        default=SyncStatus.NEVER,
    )

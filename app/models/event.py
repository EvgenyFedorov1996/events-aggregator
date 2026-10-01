from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import EventStatus

if TYPE_CHECKING:
    from app.models.place import Place
    from app.models.ticket import Ticket


class Event(Base):
    __tablename__ = "events"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    place_id: Mapped[UUID] = mapped_column(
        ForeignKey("places.id"),
        nullable=False,
    )
    event_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    registration_deadline: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    status: Mapped[EventStatus] = mapped_column(
        String(50),
        nullable=False,
    )
    number_of_visitors: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    place: Mapped["Place"] = relationship(
        back_populates="events",
    )

    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="event",
    )

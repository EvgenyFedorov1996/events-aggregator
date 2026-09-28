from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EventListItem(BaseModel):
    id: UUID
    name: str
    place: str
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class EventListResponse(BaseModel):
    count: int
    next: str | None
    previous: str | None
    results: list[EventListItem]


class PlaceDetail(BaseModel):
    id: UUID
    name: str
    address: str
    seats_pattern: str


class EventDetailResponse(BaseModel):
    id: UUID
    name: str
    place: PlaceDetail
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class AvailableSeatsResponse(BaseModel):
    seats: list[str]

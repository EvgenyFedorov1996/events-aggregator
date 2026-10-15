from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class TicketCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    seat: str
    event_id: UUID
    idempotency_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )


class TicketCreateResponse(BaseModel):
    ticket_id: UUID


class TicketDeleteResponse(BaseModel):
    success: bool

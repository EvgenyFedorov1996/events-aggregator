from uuid import UUID

from pydantic import BaseModel, EmailStr


class TicketCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    seat: str
    event_id: UUID


class TicketCreateResponse(BaseModel):
    ticket_id: UUID


class TicketDeleteResponse(BaseModel):
    success: bool
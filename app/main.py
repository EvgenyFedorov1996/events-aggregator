from contextlib import asynccontextmanager
from datetime import date
from uuid import UUID

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.seats import SeatsCache
from app.clients.events_provider import EventsProviderClient
from app.database import get_session
from app.repositories.events import EventRepository
from app.schemas.events import (
    AvailableSeatsResponse,
    EventDetailResponse,
    EventListItem,
    EventListResponse,
    PlaceDetail,
)
from app.schemas.tickets import (
    TicketCreateRequest,
    TicketCreateResponse,
    TicketDeleteResponse,
)
from app.services.exceptions import (
    EventNotFound,
    RegistrationClosed,
    SeatNotAvailable,
    TicketNotFound,
)
from app.services.tickets import create_ticket, delete_ticket
from app.workers.scheduler import (
    run_sync_job,
    start_scheduler,
    stop_scheduler,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()

    yield

    stop_scheduler()


app = FastAPI(
    title="Events Aggregator",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


@app.exception_handler(EventNotFound)
async def event_not_found_handler(
    request: Request,
    exc: EventNotFound,
):
    return JSONResponse(
        status_code=404,
        content={"detail": "Event not found"},
    )


@app.exception_handler(RegistrationClosed)
async def registration_closed_handler(
    request: Request,
    exc: RegistrationClosed,
):
    return JSONResponse(
        status_code=400,
        content={"detail": "Registration is closed"},
    )


@app.exception_handler(SeatNotAvailable)
async def seat_not_available_handler(
    request: Request,
    exc: SeatNotAvailable,
):
    return JSONResponse(
        status_code=400,
        content={"detail": "Seat is not available"},
    )


@app.exception_handler(TicketNotFound)
async def ticket_not_found_handler(
    request: Request,
    exc: TicketNotFound,
):
    return JSONResponse(
        status_code=404,
        content={"detail": "Ticket not found"},
    )


seats_cache = SeatsCache(ttl=30)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.get(
    "/api/events",
    response_model=EventListResponse,
)
async def get_events(
    date_from: date | None = None,
    page: int = 1,
    page_size: int = 20,
    session: AsyncSession = Depends(get_session),
):
    repository = EventRepository(session)

    total_count, rows = await repository.get_events(
        date_from=date_from,
        page=page,
        page_size=page_size,
    )

    events = [
        EventListItem(
            id=event.id,
            name=event.name,
            place=place.name,
            event_time=event.event_time,
            registration_deadline=event.registration_deadline,
            status=event.status,
            number_of_visitors=event.number_of_visitors,
        )
        for event, place in rows
    ]

    total_pages = (total_count + page_size - 1) // page_size

    next_page = page + 1 if page < total_pages else None
    previous_page = page - 1 if page > 1 else None

    next_url = None
    if next_page:
        if date_from is None:
            next_url = (
                f"/api/events?page={next_page}&page_size={page_size}"
            )
        else:
            next_url = (
                f"/api/events?date_from={date_from}"
                f"&page={next_page}&page_size={page_size}"
            )

    previous_url = None
    if previous_page:
        if date_from is None:
            previous_url = (
                f"/api/events?page={previous_page}&page_size={page_size}"
            )
        else:
            previous_url = (
                f"/api/events?date_from={date_from}"
                f"&page={previous_page}&page_size={page_size}"
            )

    return EventListResponse(
        count=total_count,
        next=next_url,
        previous=previous_url,
        results=events,
    )


@app.get(
    "/api/events/{event_id}",
    response_model=EventDetailResponse,
)
async def get_event(
    event_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    repository = EventRepository(session)

    row = await repository.get_event(event_id)

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    event, place = row

    return EventDetailResponse(
        id=event.id,
        name=event.name,
        place=PlaceDetail(
            id=place.id,
            name=place.name,
            address=place.address,
            seats_pattern=place.seats_pattern,
        ),
        event_time=event.event_time,
        registration_deadline=event.registration_deadline,
        status=event.status,
        number_of_visitors=event.number_of_visitors,
    )


@app.get(
    "/api/events/{event_id}/seats",
    response_model=AvailableSeatsResponse,
)
async def get_available_seats(
    event_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    repository = EventRepository(session)

    event = await repository.get_event_by_id(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    cache_key = str(event_id)
    cached_seats = seats_cache.get(cache_key)

    if cached_seats is not None:
        return AvailableSeatsResponse(
            event_id=event_id,
            available_seats=cached_seats,
        )

    client = EventsProviderClient()

    try:
        response = await client.get_available_seats(event_id)
    finally:
        await client.close()

    seats = response["seats"]
    seats_cache.set(cache_key, seats)

    return AvailableSeatsResponse(
        event_id=event_id,
        available_seats=seats,
    )


@app.post(
    "/api/tickets",
    response_model=TicketCreateResponse,
    status_code=201,
)
async def create_ticket_endpoint(
    request: TicketCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    client = EventsProviderClient()

    try:
        ticket = await create_ticket(
            session=session,
            client=client,
            event_id=request.event_id,
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            seat=request.seat,
        )

        return TicketCreateResponse(
            ticket_id=ticket.id,
        )
    finally:
        await client.close()


@app.delete(
    "/api/tickets/{ticket_id}",
    response_model=TicketDeleteResponse,
)
async def delete_ticket_endpoint(
    ticket_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    client = EventsProviderClient()

    try:
        await delete_ticket(
            session=session,
            client=client,
            ticket_id=ticket_id,
        )

        return TicketDeleteResponse(
            success=True,
        )
    finally:
        await client.close()


@app.post("/api/sync/trigger", status_code=202)
async def trigger_sync(
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(run_sync_job)

    return {"status": "accepted"}

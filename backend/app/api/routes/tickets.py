from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.core.pagination import InvalidCursorError
from app.db.session import DbSession
from app.models import Priority
from app.schemas.ticket import TicketCreate, TicketPage, TicketRead
from app.services import ticket_service
from app.services.ticket_service import TicketNotFoundError
from app.schemas.ticket import TicketAssign, TicketCreate, TicketPage, TicketRead
from app.services.ticket_service import TicketAlreadyAssignedError, TicketNotFoundError

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: DbSession) -> TicketRead:
    ticket = ticket_service.create_ticket(db, payload)
    return TicketRead.model_validate(ticket)


@router.get("")
def list_tickets(
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
    priority: Priority | None = None,
    assigned: bool | None = None,
    tag: Annotated[str | None, Query(max_length=50)] = None,
) -> TicketPage:
    try:
        items, next_cursor = ticket_service.list_tickets(
            db,
            limit=limit,
            cursor=cursor,
            priority=priority,
            assigned=assigned,
            tag=tag,
        )
    except InvalidCursorError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid cursor") from None

    return TicketPage(
        items=[TicketRead.model_validate(t) for t in items],
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, db: DbSession) -> TicketRead:
    try:
        ticket = ticket_service.get_ticket(db, ticket_id)
    except TicketNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found") from None
    return TicketRead.model_validate(ticket)


@router.post(
    "/{ticket_id}/assign",
    responses={
        404: {"description": "Ticket not found"},
        409: {"description": "Already assigned"},
    },
)
def assign_ticket(ticket_id: int, payload: TicketAssign, db: DbSession) -> TicketRead:
    try:
        ticket = ticket_service.assign_ticket(db, ticket_id, payload.email)
    except TicketNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ticket not found") from None
    except TicketAlreadyAssignedError as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Ticket is already assigned to {exc.assigned_to}"
        ) from None
    return TicketRead.model_validate(ticket)

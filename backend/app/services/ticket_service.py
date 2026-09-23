from sqlalchemy import func, select, tuple_, update
from sqlalchemy.orm import Session

from app.core.pagination import decode_cursor, encode_cursor
from app.models import Priority, Ticket
from app.schemas.ticket import TicketCreate


class TicketNotFoundError(Exception):
    """Raised when a ticket does not exist."""


def create_ticket(db: Session, data: TicketCreate) -> Ticket:
    ticket = Ticket(**data.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)  # load DB-generated values (id, created_at, updated_at)
    return ticket


def get_ticket(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError(ticket_id)
    return ticket


def list_tickets(
    db: Session,
    *,
    limit: int,
    cursor: str | None = None,
    priority: Priority | None = None,
    assigned: bool | None = None,
    tag: str | None = None,
) -> tuple[list[Ticket], str | None]:
    """Return one page of tickets, newest first, plus the cursor for the next page."""
    stmt = select(Ticket)

    if priority is not None:
        stmt = stmt.where(Ticket.priority == priority)
    if assigned is True:
        stmt = stmt.where(Ticket.assigned_to.is_not(None))
    elif assigned is False:
        stmt = stmt.where(Ticket.assigned_to.is_(None))
    if tag:
        stmt = stmt.where(Ticket.tags.contains([tag.strip().lower()]))

    if cursor:
        created_at, ticket_id = decode_cursor(cursor)
        # Keyset pagination: continue right after the last row of the previous page
        stmt = stmt.where(tuple_(Ticket.created_at, Ticket.id) < tuple_(created_at, ticket_id))

    # Fetch one extra row to know if there is a next page
    stmt = stmt.order_by(Ticket.created_at.desc(), Ticket.id.desc()).limit(limit + 1)
    rows = list(db.scalars(stmt))

    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = encode_cursor(items[-1].created_at, items[-1].id) if has_more else None
    return items, next_cursor


class TicketAlreadyAssignedError(Exception):
    """Raised when someone tries to claim a ticket that already has an owner."""

    def __init__(self, assigned_to: str | None) -> None:
        self.assigned_to = assigned_to
        super().__init__(f"Ticket is already assigned to {assigned_to}")


def assign_ticket(db: Session, ticket_id: int, email: str) -> Ticket:
    """Claim a ticket. Race-safe: only the first agent can succeed.

    The ownership check and the write happen in ONE atomic UPDATE statement,
    so two agents claiming at the same moment can never both succeed.
    """
    stmt = (
        update(Ticket)
        .where(Ticket.id == ticket_id, Ticket.assigned_to.is_(None))
        .values(assigned_to=email, assigned_at=func.now())
        .returning(Ticket)
    )
    ticket = db.scalars(stmt).one_or_none()

    if ticket is None:
        # 0 rows updated: either the ticket does not exist, or it already has an owner
        db.rollback()
        existing = db.get(Ticket, ticket_id)
        if existing is None:
            raise TicketNotFoundError(ticket_id)
        raise TicketAlreadyAssignedError(existing.assigned_to)

    db.commit()
    return ticket

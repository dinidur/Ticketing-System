import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    Identity,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Priority(enum.StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    priority: Mapped[Priority] = mapped_column(
        Enum(
            Priority,
            name="ticket_priority",
            values_callable=lambda e: [member.value for member in e],
        ),
        default=Priority.MEDIUM,
        server_default=Priority.MEDIUM.value,
    )
    tags: Mapped[list[str]] = mapped_column(ARRAY(String(50)), default=list, server_default="{}")
    assigned_to: Mapped[str | None] = mapped_column(String(320))
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        # assigned_to and assigned_at must be both set or both empty
        CheckConstraint(
            "(assigned_to IS NULL) = (assigned_at IS NULL)",
            name="assignment_consistent",
        ),
        # Pagination: ORDER BY created_at DESC, id DESC
        Index("ix_tickets_created_at_id", "created_at", "id"),
        # Filtering by priority
        Index("ix_tickets_priority", "priority"),
        # Searching inside the tags array (e.g. tags @> '{billing}')
        Index("ix_tickets_tags", "tags", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} priority={self.priority} assigned_to={self.assigned_to}>"

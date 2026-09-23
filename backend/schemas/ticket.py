from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from app.models.ticket import Priority

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=200)]
Description = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10_000)
]
Tag = Annotated[
    str,
    StringConstraints(strip_whitespace=True, to_lower=True, min_length=1, max_length=50),
]


class TicketCreate(BaseModel):
    """Request body for creating a ticket."""

    title: Title
    description: Description
    priority: Priority = Priority.MEDIUM
    tags: list[Tag] = Field(default_factory=list, max_length=10)

    @field_validator("tags")
    @classmethod
    def remove_duplicate_tags(cls, tags: list[str]) -> list[str]:
        # Keeps the original order, removes duplicates
        return list(dict.fromkeys(tags))


class TicketRead(BaseModel):
    """Ticket returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    priority: Priority
    tags: list[str]
    assigned_to: str | None
    assigned_at: datetime | None
    created_at: datetime
    updated_at: datetime

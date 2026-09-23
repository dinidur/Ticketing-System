import base64
import json
from datetime import datetime


class InvalidCursorError(ValueError):
    """Raised when a pagination cursor cannot be decoded."""


def encode_cursor(created_at: datetime, ticket_id: int) -> str:
    raw = json.dumps({"c": created_at.isoformat(), "i": ticket_id})
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
        return datetime.fromisoformat(data["c"]), int(data["i"])
    except (ValueError, KeyError, TypeError) as exc:
        raise InvalidCursorError("Invalid cursor") from exc

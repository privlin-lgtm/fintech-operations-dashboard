import base64
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, TypeVar
from uuid import UUID

from app.core.exceptions import InvalidCursorError


@dataclass(frozen=True)
class Cursor:
    """Keyset position: the (created_at, id) of the last row on the previous page.

    Encoding a position instead of an offset means a page fetch is a single
    indexed range scan regardless of how deep the caller pages — an `OFFSET n`
    still forces Postgres to walk and discard n rows first.
    """

    created_at: datetime
    id: UUID


def encode_cursor(cursor: Cursor) -> str:
    payload = {"created_at": cursor.created_at.isoformat(), "id": str(cursor.id)}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def decode_cursor(value: str) -> Cursor:
    try:
        payload = json.loads(base64.urlsafe_b64decode(value.encode()).decode())
        return Cursor(created_at=datetime.fromisoformat(payload["created_at"]), id=UUID(payload["id"]))
    except (KeyError, ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidCursorError(value) from exc


class _Keyed(Protocol):
    created_at: datetime
    id: UUID


RowT = TypeVar("RowT", bound=_Keyed)


def paginate(rows: list[RowT], limit: int) -> tuple[list[RowT], str | None]:
    """Split a (limit + 1)-sized fetch into a page plus the next cursor, if any."""
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = encode_cursor(Cursor(items[-1].created_at, items[-1].id)) if has_more and items else None
    return items, next_cursor

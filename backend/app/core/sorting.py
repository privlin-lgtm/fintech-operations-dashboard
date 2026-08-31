"""Sort parsing and sort-aware keyset cursors for list endpoints.

Default pagination elsewhere still uses (created_at, id). Customer search
needs arbitrary sort columns (FR-CS-6), so cursors here carry the active sort
and the last row's sort value plus id as a stable tiebreaker.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, TypeVar
from uuid import UUID

from app.core.exceptions import InvalidCursorError, ValidationConflictError


@dataclass(frozen=True)
class SortSpec:
    field: str
    descending: bool

    @property
    def raw(self) -> str:
        return f"-{self.field}" if self.descending else self.field


def parse_sort(raw: str, *, allowed: set[str]) -> SortSpec:
    descending = raw.startswith("-")
    field = raw[1:] if descending else raw
    if field not in allowed:
        raise ValidationConflictError(
            f"Unsupported sort field {field!r}; allowed: {sorted(allowed)}"
        )
    return SortSpec(field=field, descending=descending)


@dataclass(frozen=True)
class SortCursor:
    sort: str
    sort_value: str
    id: UUID


def encode_sort_cursor(cursor: SortCursor) -> str:
    payload = {"sort": cursor.sort, "sort_value": cursor.sort_value, "id": str(cursor.id)}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def decode_sort_cursor(value: str, *, expected_sort: str) -> SortCursor:
    try:
        payload = json.loads(base64.urlsafe_b64decode(value.encode()).decode())
        cursor = SortCursor(
            sort=payload["sort"],
            sort_value=payload["sort_value"],
            id=UUID(payload["id"]),
        )
    except (KeyError, ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise InvalidCursorError(value) from exc

    if cursor.sort != expected_sort:
        raise InvalidCursorError(value)
    return cursor


def serialize_sort_value(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


class _SortKeyed(Protocol):
    id: UUID


RowT = TypeVar("RowT", bound=_SortKeyed)


def paginate_sorted(
    rows: list[RowT],
    limit: int,
    *,
    sort: str,
    get_sort_value: Callable[[RowT], Any],
) -> tuple[list[RowT], str | None]:
    has_more = len(rows) > limit
    items = rows[:limit]
    if not has_more or not items:
        return items, None
    last = items[-1]
    next_cursor = encode_sort_cursor(
        SortCursor(
            sort=sort,
            sort_value=serialize_sort_value(get_sort_value(last)),
            id=last.id,
        )
    )
    return items, next_cursor

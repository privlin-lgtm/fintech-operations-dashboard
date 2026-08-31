from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.exceptions import InvalidCursorError
from app.core.pagination import Cursor, decode_cursor, encode_cursor, paginate


@dataclass
class Row:
    created_at: datetime
    id: object


def test_encode_decode_roundtrip():
    now = datetime.now(UTC)
    cid = uuid4()
    cursor = Cursor(created_at=now, id=cid)

    decoded = decode_cursor(encode_cursor(cursor))

    assert decoded.created_at == now
    assert decoded.id == cid


def test_decode_rejects_garbage():
    with pytest.raises(InvalidCursorError):
        decode_cursor("not-base64-json")


def test_decode_rejects_valid_base64_wrong_shape():
    import base64
    import json

    bad = base64.urlsafe_b64encode(json.dumps({"nope": 1}).encode()).decode()
    with pytest.raises(InvalidCursorError):
        decode_cursor(bad)


def test_paginate_no_more_pages():
    now = datetime.now(UTC)
    rows = [Row(created_at=now, id=uuid4()) for _ in range(3)]

    items, next_cursor = paginate(rows, limit=5)

    assert items == rows
    assert next_cursor is None


def test_paginate_has_more_pages_returns_cursor_from_last_kept_row():
    now = datetime.now(UTC)
    rows = [Row(created_at=now - timedelta(seconds=i), id=uuid4()) for i in range(6)]

    items, next_cursor = paginate(rows, limit=5)

    assert len(items) == 5
    assert items == rows[:5]
    assert next_cursor is not None
    decoded = decode_cursor(next_cursor)
    assert decoded.created_at == items[-1].created_at
    assert decoded.id == items[-1].id


def test_paginate_exact_limit_has_no_next_page():
    now = datetime.now(UTC)
    rows = [Row(created_at=now, id=uuid4()) for _ in range(5)]

    items, next_cursor = paginate(rows, limit=5)

    assert len(items) == 5
    assert next_cursor is None

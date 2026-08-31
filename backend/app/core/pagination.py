import base64
import json
from typing import Any


def encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(json.dumps({"offset": offset}).encode()).decode()


def decode_cursor(cursor: str) -> int:
    try:
        payload: dict[str, Any] = json.loads(
            base64.urlsafe_b64decode(cursor.encode()).decode()
        )
        return int(payload["offset"])
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid cursor") from exc

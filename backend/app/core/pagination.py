import base64
import binascii
from datetime import datetime

from app.core.exceptions import AppError


class InvalidCursorError(AppError):
    status_code = 400
    error_type = "invalid-cursor"
    title = "Invalid pagination cursor"


def encode_cursor(created_at: datetime, item_id: str) -> str:
    raw = f"{created_at.isoformat()}|{item_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


_MAX_CURSOR_LEN = 200  # base64(datetime|uuid) is ~92 chars; 200 is a safe ceiling


def decode_cursor(cursor: str) -> tuple[datetime, str]:
    if len(cursor) > _MAX_CURSOR_LEN:
        raise InvalidCursorError("The provided cursor could not be decoded")
    try:
        raw = base64.urlsafe_b64decode(cursor.encode()).decode()
        created_at_str, item_id = raw.split("|", 1)
        return datetime.fromisoformat(created_at_str), item_id
    except (ValueError, binascii.Error) as exc:
        raise InvalidCursorError("The provided cursor could not be decoded") from exc

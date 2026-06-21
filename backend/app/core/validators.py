"""Shared input-validation utilities used across DTOs and API routes.

All functions raise ``ValueError`` on bad input so they integrate naturally
with Pydantic field_validators (which re-raise as ``ValidationError``).
"""

from __future__ import annotations

import re
import uuid
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# ------------------------------------------------------------------
# String sanitisation
# ------------------------------------------------------------------

_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def strip_control_chars(value: str) -> str:
    """Remove ASCII control characters (NUL, BEL, BS, etc.) that have no
    legitimate use in user-supplied text and can confuse downstream renderers
    or log parsers."""
    return _CTRL_RE.sub("", value)


def sanitize_text(value: str | None, *, max_length: int) -> str | None:
    """Strip whitespace + control chars; enforce max byte length.

    Returns ``None`` if the cleaned value is empty.  Raises ``ValueError``
    if the value exceeds ``max_length`` characters after cleaning.
    """
    if value is None:
        return None
    cleaned = strip_control_chars(value).strip()
    if not cleaned:
        return None
    if len(cleaned) > max_length:
        raise ValueError(f"Value exceeds {max_length} characters (got {len(cleaned)})")
    return cleaned


def sanitize_list(
    items: list[str] | None,
    *,
    max_items: int,
    max_item_length: int,
) -> list[str] | None:
    """Deduplicate, strip, and size-limit a list of text items."""
    if items is None:
        return None
    if len(items) > max_items:
        raise ValueError(f"List exceeds {max_items} items (got {len(items)})")
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in items:
        item = strip_control_chars(raw).strip()
        if not item:
            continue
        if len(item) > max_item_length:
            raise ValueError(f"Item exceeds {max_item_length} characters: {item!r}")
        if item not in seen:
            seen.add(item)
            cleaned.append(item)
    return cleaned


# ------------------------------------------------------------------
# Structured-type validation
# ------------------------------------------------------------------

def validate_uuid(value: str) -> str:
    """Raise ``ValueError`` if ``value`` is not a valid UUID string."""
    try:
        uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Invalid UUID format: {value!r}") from exc
    return value


def validate_timezone(value: str) -> str:
    """Raise ``ValueError`` if ``value`` is not a valid IANA timezone identifier."""
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, KeyError) as exc:
        raise ValueError(f"Unknown timezone: {value!r}") from exc
    return value


def validate_url_scheme(
    value: str | None,
    *,
    allowed: tuple[str, ...] = ("https", "http"),
) -> str | None:
    """Reject non-HTTP(S) URLs such as ``javascript:``, ``data:``, ``file:``."""
    if value is None:
        return None
    scheme = urlparse(value).scheme.lower()
    if scheme not in allowed:
        raise ValueError(f"URL must use one of {allowed!r} (got {scheme!r})")
    return value


# ------------------------------------------------------------------
# SQL LIKE wildcard escaping
# ------------------------------------------------------------------

def escape_like(term: str, escape_char: str = "\\") -> str:
    """Escape the LIKE special characters ``%``, ``_``, and the escape char
    itself so that user input is treated as a literal substring pattern.

    Use together with the SQLAlchemy ``escape=`` keyword:
      ``col.ilike(f"%{escape_like(q)}%", escape="\\\\")``

    Without escaping, a query like ``%a%b%c%`` causes a catastrophically
    expensive cross-product scan on large tables.
    """
    return (
        term.replace(escape_char, escape_char * 2)
        .replace("%", f"{escape_char}%")
        .replace("_", f"{escape_char}_")
    )

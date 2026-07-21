"""Trustworthy client-IP resolution behind a reverse proxy.

``X-Forwarded-For`` is a client-supplied header. Every entry in it is
attacker-controlled *except* the ones appended by proxies we actually run
behind. Reading the leftmost entry — the common default, and what uvicorn's
``--forwarded-allow-ips='*'`` does — hands an attacker full control of the
address the application believes it is talking to, which defeats every
IP-keyed control (rate limiting, abuse counters) and forges the ``client_ip``
recorded in security logs.

The only safe read is positional: count back from the *right*, because each
proxy appends the address it received the connection from. With exactly one
trusted proxy in front of the app (Render's TLS terminator), the last entry is
the address that proxy observed, and nothing the client sends can displace it.

``TRUSTED_PROXY_HOPS`` must equal the number of proxies that append to the
header. Set it to 0 when the app is reachable directly, in which case the
header is ignored entirely and the peer address is used.
"""

from __future__ import annotations

import ipaddress

from fastapi import Request

from app.core.config import get_settings

_UNKNOWN = "unknown"


def _normalize(candidate: str) -> str | None:
    """Return a valid IP from one X-Forwarded-For element, or None.

    Handles bare IPs, IPv4 ``host:port``, and bracketed IPv6 ``[host]:port``.
    Anything that does not parse as an IP address is rejected rather than
    passed through, so a crafted entry cannot become a rate-limit bucket key.
    """
    value = candidate.strip()
    if not value:
        return None

    if value.startswith("["):
        end = value.find("]")
        if end != -1:
            value = value[1:end]
    elif value.count(":") == 1:
        # Exactly one colon means IPv4:port (bare IPv6 has several).
        value = value.rsplit(":", 1)[0]

    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def get_client_ip(request: Request) -> str:
    """Resolve the caller's IP address, honoring only trusted proxy hops."""
    peer = request.client.host if request.client else None
    hops = get_settings().trusted_proxy_hops

    if hops <= 0:
        return peer or _UNKNOWN

    # A client may send several X-Forwarded-For headers; proxies treat them as
    # one comma-joined list, so we must too, or an attacker could split the
    # chain to shift which element lands at the trusted position.
    forwarded = request.headers.getlist("x-forwarded-for")
    if not forwarded:
        return peer or _UNKNOWN

    chain = [part for raw in forwarded for part in raw.split(",")]

    # Fewer entries than trusted hops means the request did not traverse the
    # proxies we expect. Trusting any entry here would accept a forged chain,
    # so fall back to the peer address.
    if len(chain) < hops:
        return peer or _UNKNOWN

    return _normalize(chain[-hops]) or peer or _UNKNOWN

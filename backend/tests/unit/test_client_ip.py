"""Client-IP resolution must not be forgeable via X-Forwarded-For.

Regression tests for the rate-limit bypass: reading the leftmost X-Forwarded-For
entry let any caller pick their own rate-limit bucket (and their own client_ip
in the security logs) by sending a header.
"""

import pytest
from fastapi import Request

from app.core.client_ip import get_client_ip
from app.core.config import get_settings

PROXY = "10.0.0.1"
REAL_CLIENT = "203.0.113.9"
SPOOFED = "198.51.100.200"


def _request(headers: list[tuple[bytes, bytes]], peer: str = PROXY) -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": headers,
            "client": (peer, 4444),
        }
    )


@pytest.fixture
def _one_hop() -> None:
    """Run as if behind exactly one trusted proxy (the production setting)."""
    settings = get_settings()
    original = settings.trusted_proxy_hops
    object.__setattr__(settings, "trusted_proxy_hops", 1)
    yield
    object.__setattr__(settings, "trusted_proxy_hops", original)


def test_uses_proxy_appended_entry_not_client_supplied_one(_one_hop: None) -> None:
    """The attacker's value sits left of the entry the proxy appended."""
    request = _request([(b"x-forwarded-for", f"{SPOOFED}, {REAL_CLIENT}".encode())])
    assert get_client_ip(request) == REAL_CLIENT


def test_split_header_cannot_shift_the_trusted_position(_one_hop: None) -> None:
    """Multiple X-Forwarded-For headers are one logical chain, not separate ones."""
    request = _request(
        [
            (b"x-forwarded-for", SPOOFED.encode()),
            (b"x-forwarded-for", REAL_CLIENT.encode()),
        ]
    )
    assert get_client_ip(request) == REAL_CLIENT


def test_single_entry_is_the_proxy_appended_client(_one_hop: None) -> None:
    """Normal case: no inbound header, so the proxy's entry is the only one."""
    request = _request([(b"x-forwarded-for", REAL_CLIENT.encode())])
    assert get_client_ip(request) == REAL_CLIENT


def test_short_chain_falls_back_to_peer(_one_hop: None) -> None:
    """A chain shorter than the trusted hop count did not traverse our proxies."""
    request = _request([])
    assert get_client_ip(request) == PROXY


def test_garbage_entry_falls_back_to_peer(_one_hop: None) -> None:
    """A non-IP value must never become a rate-limit bucket key."""
    request = _request([(b"x-forwarded-for", b"not-an-ip")])
    assert get_client_ip(request) == PROXY


def test_port_is_stripped(_one_hop: None) -> None:
    """host:port and [v6]:port must normalize to the bare address, so the same
    client cannot occupy many buckets by varying its source port."""
    assert get_client_ip(_request([(b"x-forwarded-for", b"203.0.113.9:51000")])) == REAL_CLIENT
    assert get_client_ip(_request([(b"x-forwarded-for", b"[2001:db8::1]:443")])) == "2001:db8::1"


def test_header_ignored_when_not_behind_a_proxy() -> None:
    """With hops=0 (the default) the header is untrusted input and is ignored."""
    request = _request([(b"x-forwarded-for", SPOOFED.encode())], peer=REAL_CLIENT)
    assert get_client_ip(request) == REAL_CLIENT

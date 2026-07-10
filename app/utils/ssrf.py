"""SSRF protection for server-side fetches.

Whoogle proxies remote resources (the /element image proxy and the /window
page proxy) by fetching an attacker-supplied URL server-side. Without
restriction, an anonymous request can point those routes at loopback,
link-local, or RFC1918 addresses -- or a hostname such as ``127-0-0-1.nip.io``
that *looks* like a public domain but resolves to an internal IP -- and use the
Whoogle host as a proxy into the internal network or the cloud metadata
endpoint (169.254.169.254).

This module resolves the target host and rejects any request that would reach a
non-public address. Because the shared HTTP client follows redirects, the guard
is enforced as an httpx request event hook so that *every* hop (including
redirect targets) is re-validated, not just the first URL.
"""

import ipaddress
import os
import socket
import urllib.parse as urlparse
from typing import Iterable

import httpx


class SSRFError(httpx.RequestError):
    """Raised when a request targets a non-public / disallowed address.

    Subclasses ``httpx.RequestError`` (and therefore ``httpx.HTTPError``) so it
    is caught by the existing ``except httpx.HTTPError`` handlers in the proxy
    routes and surfaces as a normal "could not fetch" outcome.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


ALLOWED_SCHEMES = ('http', 'https')


def _allowlisted_hosts() -> set:
    """Hostnames an operator has explicitly opted to allow reaching internally.

    Set ``WHOOGLE_ALLOW_INTERNAL_HOSTS`` to a comma-separated list of hostnames
    to permit fetching them even if they resolve to a private address (e.g. a
    self-hoster proxying a service on their LAN). Empty by default -- the
    secure-by-default posture blocks all internal targets.
    """
    raw = os.environ.get('WHOOGLE_ALLOW_INTERNAL_HOSTS', '')
    return {h.strip().lower() for h in raw.split(',') if h.strip()}


def _ip_is_blocked(ip_str: str) -> bool:
    """True if the address is not a routable public address."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        # Unparseable address -- fail closed.
        return True

    # Unwrap IPv4-mapped IPv6 (e.g. ::ffff:127.0.0.1) so the mapped v4 address
    # is classified rather than the wrapper.
    if ip.version == 6 and getattr(ip, 'ipv4_mapped', None) is not None:
        ip = ip.ipv4_mapped

    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local      # 169.254.0.0/16 -> cloud metadata, fe80::/10
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _resolve(host: str) -> Iterable[str]:
    """Resolve a host to every IP it maps to (fails closed on error)."""
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError, OSError):
        raise SSRFError(f'Could not resolve host: {host!r}')
    return {info[4][0] for info in infos}


def is_safe_url(url: str) -> bool:
    """Return True only if *url* is http(s) and resolves to public IPs."""
    try:
        guard_url(url)
        return True
    except SSRFError:
        return False


def guard_url(url: str) -> None:
    """Validate *url*; raise :class:`SSRFError` if it must not be fetched.

    Rejects:
      * non-http(s) schemes (file://, gopher://, ftp://, ...)
      * missing/empty host
      * a host that resolves to *any* non-public address
        (loopback, RFC1918, link-local/metadata, reserved, multicast).

    If any resolved address is internal the whole URL is rejected, so an
    attacker cannot smuggle an internal IP alongside a public one in DNS.
    """
    if not url:
        raise SSRFError('Empty URL')

    parsed = urlparse.urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise SSRFError(f'Disallowed scheme: {parsed.scheme!r}')

    host = parsed.hostname
    if not host:
        raise SSRFError('URL has no host')

    if host.lower() in _allowlisted_hosts():
        return

    for ip_str in _resolve(host):
        if _ip_is_blocked(ip_str):
            raise SSRFError(
                f'Refusing to fetch {host!r}: resolves to non-public '
                f'address {ip_str}')


def ssrf_request_hook(request: 'httpx.Request') -> None:
    """httpx request event hook enforcing :func:`guard_url` on every hop.

    Registered on the shared client so redirect targets are re-validated, not
    just the initial URL.
    """
    guard_url(str(request.url))

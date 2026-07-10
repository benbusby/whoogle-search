import socket

import httpx
import pytest

from app.utils import ssrf
from app.utils.ssrf import (
    SSRFError,
    guard_url,
    is_safe_url,
    ssrf_request_hook,
    _ip_is_blocked,
)


def _fake_resolver(mapping):
    """Return a getaddrinfo stand-in that maps host -> list of IPs."""
    def _getaddrinfo(host, *args, **kwargs):
        if host not in mapping:
            raise socket.gaierror('name resolution failed')
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (ip, 0))
                for ip in mapping[host]]
    return _getaddrinfo


@pytest.mark.parametrize('ip', [
    '127.0.0.1',            # loopback
    '10.0.0.5',            # RFC1918
    '192.168.1.1',         # RFC1918
    '172.16.0.1',          # RFC1918
    '169.254.169.254',     # cloud metadata (link-local)
    '0.0.0.0',             # unspecified
    '::1',                 # IPv6 loopback
    'fe80::1',             # IPv6 link-local
    '::ffff:127.0.0.1',    # IPv4-mapped loopback
])
def test_internal_addresses_blocked(ip):
    assert _ip_is_blocked(ip) is True


@pytest.mark.parametrize('ip', ['93.184.216.34', '8.8.8.8', '1.1.1.1'])
def test_public_addresses_allowed(ip):
    assert _ip_is_blocked(ip) is False


def test_guard_rejects_loopback_hostname(monkeypatch):
    # A "valid domain" that resolves to loopback (the nip.io bypass class).
    monkeypatch.setattr(
        socket, 'getaddrinfo',
        _fake_resolver({'127-0-0-1.nip.io': ['127.0.0.1']}))
    with pytest.raises(SSRFError):
        guard_url('http://127-0-0-1.nip.io/secret')
    assert is_safe_url('http://127-0-0-1.nip.io/secret') is False


def test_guard_rejects_metadata_host(monkeypatch):
    monkeypatch.setattr(
        socket, 'getaddrinfo',
        _fake_resolver({'meta.evil.com': ['169.254.169.254']}))
    assert is_safe_url('http://meta.evil.com/latest/meta-data/') is False


def test_guard_allows_public_host(monkeypatch):
    monkeypatch.setattr(
        socket, 'getaddrinfo',
        _fake_resolver({'example.com': ['93.184.216.34']}))
    assert is_safe_url('https://example.com/logo.png') is True
    guard_url('https://example.com/logo.png')  # does not raise


def test_guard_rejects_mixed_public_and_internal(monkeypatch):
    # DNS returning one public + one internal address must still be blocked.
    monkeypatch.setattr(
        socket, 'getaddrinfo',
        _fake_resolver({'rebind.evil.com': ['93.184.216.34', '127.0.0.1']}))
    assert is_safe_url('http://rebind.evil.com/') is False


def test_guard_rejects_non_http_scheme():
    with pytest.raises(SSRFError):
        guard_url('file:///etc/passwd')
    with pytest.raises(SSRFError):
        guard_url('gopher://127.0.0.1:6379/_')


def test_guard_rejects_empty_and_hostless():
    with pytest.raises(SSRFError):
        guard_url('')
    with pytest.raises(SSRFError):
        guard_url('http:///nohost')


def test_allowlist_env_permits_internal(monkeypatch):
    monkeypatch.setenv('WHOOGLE_ALLOW_INTERNAL_HOSTS', 'intranet.local')
    monkeypatch.setattr(
        socket, 'getaddrinfo',
        _fake_resolver({'intranet.local': ['10.1.2.3']}))
    # Allowlisted host bypasses the resolver check entirely.
    assert is_safe_url('http://intranet.local/dashboard') is True


def test_request_hook_blocks_redirect_to_internal(monkeypatch):
    # Simulates httpx invoking the event hook for a redirect hop to loopback.
    monkeypatch.setattr(
        socket, 'getaddrinfo',
        _fake_resolver({'127-0-0-1.nip.io': ['127.0.0.1']}))
    req = httpx.Request('GET', 'http://127-0-0-1.nip.io/secret')
    with pytest.raises(SSRFError):
        ssrf_request_hook(req)


def test_ssrferror_is_httpx_error():
    # Must be catchable by existing `except httpx.HTTPError` handlers.
    assert issubclass(SSRFError, httpx.HTTPError)


def test_element_route_blocks_loopback_without_fetching(client, monkeypatch):
    """End-to-end: /element must not fetch a host that resolves to loopback."""
    from app.request import Request

    monkeypatch.setattr(
        socket, 'getaddrinfo',
        _fake_resolver({'internal.test': ['127.0.0.1']}))

    calls = []

    def spy_send(self, *args, **kwargs):
        calls.append(kwargs.get('base_url', args[0] if args else None))
        raise AssertionError('send() must not be reached for a blocked target')

    monkeypatch.setattr(Request, 'send', spy_send)

    resp = client.get('/element?url=http://internal.test/secret&type=image/png')

    assert resp.status_code == 200          # served the empty gif, not the secret
    assert resp.data[:6] in (b'GIF87a', b'GIF89a')
    assert calls == []                      # server never made the internal request

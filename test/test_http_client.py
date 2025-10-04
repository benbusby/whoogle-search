import types

import httpx
import pytest

from app.services.http_client import HttpxClient


def test_httpxclient_follow_redirects_and_proxy(monkeypatch):
    calls = []

    class FakeClient:
        def __init__(self, *args, **kwargs):
            calls.append(kwargs)
        def get(self, *args, **kwargs):
            class R:
                status_code = 200
                text = ''
            return R()
        def close(self):
            pass

    monkeypatch.setattr(httpx, 'Client', FakeClient)

    proxies = {'http': 'socks5://127.0.0.1:9050', 'https': 'socks5://127.0.0.1:9050'}
    client = HttpxClient(proxies=proxies)

    # Ensure the constructor attempted to set follow_redirects and one of proxy/proxies
    assert len(calls) == 1
    kwargs = calls[0]
    assert kwargs.get('follow_redirects') is True
    assert ('proxy' in kwargs) or ('proxies' in kwargs) or ('mounts' in kwargs)


import pytest

from app import app
from app.request import Request, TorError
from app.models.config import Config


class FakeResponse:
    def __init__(self, text: str = '', status_code: int = 200, content: bytes = b''):
        self.text = text
        self.status_code = status_code
        self.content = content or b''


class FakeHttpClient:
    def __init__(self, tor_ok: bool):
        self._tor_ok = tor_ok

    def get(self, url, headers=None, cookies=None, retries=0, backoff_seconds=0.5, use_cache=False):
        if 'check.torproject.org' in url:
            return FakeResponse(text=('Congratulations' if self._tor_ok else 'Not Tor'))
        return FakeResponse(text='', status_code=200, content=b'OK')

    def close(self):
        pass


def build_config(tor: bool) -> Config:
    # Minimal config with tor flag
    with app.app_context():
        return Config(**{'tor': tor})


def test_tor_validation_success(monkeypatch):
    # Prevent real Tor signal attempts
    monkeypatch.setattr('app.request.send_tor_signal', lambda signal: True)
    cfg = build_config(tor=True)
    req = Request(normal_ua='TestUA', root_path='http://localhost:5000', config=cfg, http_client=FakeHttpClient(tor_ok=True))
    # Avoid sending a Tor NEWNYM/HEARTBEAT in unit tests by setting attempt>0 false path
    resp = req.send(base_url='https://example.com', query='')
    assert req.tor_valid is True
    assert resp.status_code == 200


def test_tor_validation_failure(monkeypatch):
    # Prevent real Tor signal attempts
    monkeypatch.setattr('app.request.send_tor_signal', lambda signal: True)
    cfg = build_config(tor=True)
    req = Request(normal_ua='TestUA', root_path='http://localhost:5000', config=cfg, http_client=FakeHttpClient(tor_ok=False))
    with pytest.raises(TorError):
        _ = req.send(base_url='https://example.com', query='')


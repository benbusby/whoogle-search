from app import app
from app.request import Request
from app.utils.session import generate_key
from test.mock_google import build_mock_response
import httpx
import pytest
import random

demo_config = {
    'near': random.choice(['Seattle', 'New York', 'San Francisco']),
    'nojs': str(random.getrandbits(1)),
    'lang_interface': random.choice(app.config['LANGUAGES'])['value'],
    'lang_search': random.choice(app.config['LANGUAGES'])['value'],
    'country': random.choice(app.config['COUNTRIES'])['value']
}


@pytest.fixture(autouse=True)
def mock_google(monkeypatch):
    original_send = Request.send

    def fake_send(self, base_url='', query='', attempt=0,
                  force_mobile=False, user_agent=''):
        use_mock = not base_url or 'google.com/search' in base_url
        if not use_mock:
            return original_send(self, base_url, query, attempt,
                                 force_mobile, user_agent)

        html = build_mock_response(query, getattr(self, 'language', ''), getattr(self, 'country', ''))
        request_url = (base_url or self.search_url) + query
        request = httpx.Request('GET', request_url)
        return httpx.Response(200, request=request, text=html)

    def fake_autocomplete(self, q):
        normalized = q.replace('+', ' ').lower()
        suggestions = []
        if 'green eggs and' in normalized:
            suggestions.append('green eggs and ham')
        if 'the cat in the' in normalized:
            suggestions.append('the cat in the hat')
        if normalized.startswith('who'):
            suggestions.extend(['whoogle', 'whoogle search'])
        return suggestions

    monkeypatch.setattr(Request, 'send', fake_send)
    monkeypatch.setattr(Request, 'autocomplete', fake_autocomplete)
    yield


@pytest.fixture
def client():
    with app.test_client() as client:
        with client.session_transaction() as session:
            session['uuid'] = 'test'
            session['key'] = app.enc_key
            session['config'] = {}
            session['auth'] = False
        yield client

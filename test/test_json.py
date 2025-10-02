import json
import types

import pytest

from app.models.endpoint import Endpoint
from app.utils import search as search_mod


@pytest.fixture
def stubbed_search_response(monkeypatch):
    # Stub Search.new_search_query to return a stable query
    def fake_new_query(self):
        self.query = 'whoogle'
        return self.query

    # Return a minimal filtered HTML snippet with a couple of links
    html = (
        '<div id="main">'
        '  <a href="https://example.com/page">Example Page</a>'
        '  <a href="/relative">Relative</a>'
        '  <a href="https://example.org/other">Other</a>'
        '</div>'
    )

    def fake_generate(self):
        return html

    monkeypatch.setattr(search_mod.Search, 'new_search_query', fake_new_query)
    monkeypatch.setattr(search_mod.Search, 'generate_response', fake_generate)


def test_search_json_accept(client, stubbed_search_response):
    rv = client.get(f'/{Endpoint.search}?q=whoogle', headers={'Accept': 'application/json'})
    assert rv._status_code == 200
    data = json.loads(rv.data)
    assert data['query'] == 'whoogle'
    assert isinstance(data['results'], list)
    hrefs = {item['href'] for item in data['results']}
    assert 'https://example.com/page' in hrefs
    assert 'https://example.org/other' in hrefs
    # Relative href should be excluded
    assert not any(href.endswith('/relative') for href in hrefs)
    # Verify new fields are present while maintaining backward compatibility
    for result in data['results']:
        assert 'href' in result
        assert 'text' in result  # Original field maintained
        assert 'title' in result  # New field
        assert 'content' in result  # New field


def test_search_json_format_param(client, stubbed_search_response):
    rv = client.get(f'/{Endpoint.search}?q=whoogle&format=json')
    assert rv._status_code == 200
    data = json.loads(rv.data)
    assert data['query'] == 'whoogle'
    assert len(data['results']) >= 2


def test_search_json_feeling_lucky(client, monkeypatch):
    # Force query to be interpreted as feeling lucky and return a redirect URL
    def fake_new_query(self):
        self.query = 'whoogle !'
        # emulate behavior of new_search_query setting feeling_lucky
        self.feeling_lucky = True
        return self.query

    def fake_generate(self):
        return 'https://example.com/lucky'

    monkeypatch.setattr(search_mod.Search, 'new_search_query', fake_new_query)
    monkeypatch.setattr(search_mod.Search, 'generate_response', fake_generate)

    rv = client.get(f'/{Endpoint.search}?q=whoogle%20!', headers={'Accept': 'application/json'})
    assert rv._status_code == 303
    data = json.loads(rv.data)
    assert data['redirect'] == 'https://example.com/lucky'



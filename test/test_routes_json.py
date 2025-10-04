import json

import pytest

from app.models.endpoint import Endpoint
from app.utils import search as search_mod


def test_captcha_json_block(client, monkeypatch):
    def fake_new_query(self):
        self.query = 'test'
        return self.query

    def fake_generate(self):
        # Inject a captcha marker into HTML so route returns 503 JSON
        return '<div>div class="g-recaptcha"</div>'

    monkeypatch.setattr(search_mod.Search, 'new_search_query', fake_new_query)
    monkeypatch.setattr(search_mod.Search, 'generate_response', fake_generate)

    rv = client.get(f'/{Endpoint.search}?q=test&format=json')
    assert rv._status_code == 503
    data = json.loads(rv.data)
    assert data['blocked'] is True
    assert 'error_message' in data


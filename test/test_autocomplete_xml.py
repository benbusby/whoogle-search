from app import app
from app.request import Request
from app.models.config import Config


class FakeHttpClient:
    def get(self, url, headers=None, cookies=None, retries=0, backoff_seconds=0.5, use_cache=False):
        # Minimal XML in Google Toolbar Autocomplete format
        xml = (
            '<?xml version="1.0"?>\n'
            '<topp>\n'
            '  <CompleteSuggestion><suggestion data="whoogle"/></CompleteSuggestion>\n'
            '  <CompleteSuggestion><suggestion data="whoogle search"/></CompleteSuggestion>\n'
            '</topp>'
        )
        class R:
            text = xml
        return R()

    def close(self):
        pass


def test_autocomplete_parsing():
    with app.app_context():
        cfg = Config(**{})
    req = Request(normal_ua='UA', root_path='http://localhost:5000', config=cfg, http_client=FakeHttpClient())
    suggestions = req.autocomplete('who')
    assert 'whoogle' in suggestions
    assert 'whoogle search' in suggestions


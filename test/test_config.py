from app import app
from app.models.config import Config


def test_preferences_token_only_includes_safe_keys(monkeypatch):
    monkeypatch.setenv('WHOOGLE_CSE_API_KEY', 'cse-secret')
    monkeypatch.setenv('WHOOGLE_CSE_ID', 'cse-id')
    monkeypatch.setenv('WHOOGLE_CONFIG_PREFERENCES_KEY', 'preferences-secret')
    monkeypatch.setenv('WHOOGLE_CONFIG_PREFERENCES_ENCRYPTED', '0')

    with app.app_context():
        config = Config()
        decoded_preferences = config._decode_preferences(config.preferences)

    assert set(decoded_preferences) == set(config.safe_keys)
    assert decoded_preferences['theme'] == config.theme
    assert 'cse_api_key' not in decoded_preferences
    assert 'cse_id' not in decoded_preferences
    assert 'preferences_key' not in decoded_preferences

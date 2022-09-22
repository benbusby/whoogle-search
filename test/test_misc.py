from cryptography.fernet import Fernet

from app import app
from app.models.endpoint import Endpoint
from app.utils.session import generate_user_key, valid_user_session


JAPAN_PREFS = 'uG-gGIJwHdqxl6DrS3mnu_511HlQcRpxYlG03Xs-' \
   + '_znXNiJWI9nLOkRLkiiFwIpeUYMTGfUF5-t9fP5DGmzDLEt04DCx703j3nPf' \
   + '29v_RWkU7gXw_44m2oAFIaKGmYlu4Z0bKyu9k5WXfL9Dy6YKKnpcR5CiaFsG' \
   + 'rccNRkAPYm-eYGAFUV8M59f8StsGd_M-gHKGS9fLok7EhwBWjHxBJ2Kv8hsT' \
   + '87zftP2gMJOevTdNnezw2Y5WOx-ZotgeheCW1BYCFcRqatlov21PHp22NGVG' \
   + '8ZuBNAFW0bE99WSdyT7dUIvzeWCLJpbdSsq-3FUUZkxbRdFYlGd8vY1UgVAp' \
   + 'OSie2uAmpgLFXygO-VfNBBZ68Q7gAap2QtzHCiKD5cFYwH3LPgVJ-DoZvJ6k' \
   + 'alt34TaYiJphgiqFKV4SCeVmLWTkr0SF3xakSR78yYJU_d41D2ng-TojA9XZ' \
   + 'uR2ZqjSvPKOWvjimu89YhFOgJxG1Po8Henj5h9OL9VXXvdvlJwBSAKw1E3FV' \
   + '7UHWiglMxPblfxqou1cYckMYkFeIMCD2SBtju68mBiQh2k328XRPTsQ_ocby' \
   + 'cgVKnleGperqbD6crRk3Z9xE5sVCjujn9JNVI-7mqOITMZ0kntq9uJ3R5n25' \
   + 'Vec0TJ0P19nEtvjY0nJIrIjtnBg=='


def test_generate_user_keys():
    key = generate_user_key()
    assert Fernet(key)
    assert generate_user_key() != key


def test_valid_session(client):
    assert not valid_user_session({'key': '', 'config': {}})
    with client.session_transaction() as session:
        assert valid_user_session(session)


def test_valid_translation_keys(client):
    valid_lang_keys = [_['value'] for _ in app.config['LANGUAGES']]
    en_keys = app.config['TRANSLATIONS']['lang_en'].keys()
    for translation_key in app.config['TRANSLATIONS']:
        # Ensure the translation is using a valid language value
        assert translation_key in valid_lang_keys

        # Ensure all translations match the same size/content of the original
        # English translation
        assert app.config['TRANSLATIONS'][translation_key].keys() == en_keys


def test_query_decryption(client):
    # FIXME: Handle decryption errors in search.py and rewrite test
    # This previously was used to test swapping decryption keys between
    # queries. While this worked in theory and usually didn't cause problems,
    # they were tied to session IDs and those are really unreliable (meaning
    # that occasionally page navigation would break).
    rv = client.get('/')
    cookie = rv.headers['Set-Cookie']

    rv = client.get(f'/{Endpoint.search}?q=test+1', headers={'Cookie': cookie})
    assert rv._status_code == 200

    with client.session_transaction() as session:
        assert valid_user_session(session)

    rv = client.get(f'/{Endpoint.search}?q=test+2', headers={'Cookie': cookie})
    assert rv._status_code == 200

    with client.session_transaction() as session:
        assert valid_user_session(session)


def test_prefs_url(client):
    base_url = f'/{Endpoint.search}?q=wikipedia'
    rv = client.get(base_url)
    assert rv._status_code == 200
    assert b'wikipedia.org' in rv.data
    assert b'ja.wikipedia.org' not in rv.data

    rv = client.get(f'{base_url}&preferences={JAPAN_PREFS}')
    assert rv._status_code == 200
    assert b'ja.wikipedia.org' in rv.data


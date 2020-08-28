from cryptography.fernet import Fernet
from flask import current_app as app

REQUIRED_SESSION_VALUES = ['uuid', 'config', 'fernet_keys']
BLACKLIST = [
    'ad', 'anuncio', 'annuncio', 'annonce', 'Anzeige', '广告', '廣告', 'Reklama', 'Реклама', 'Anunț', '광고',
    'annons', 'Annonse', 'Iklan', '広告', 'Augl.', 'Mainos', 'Advertentie', 'إعلان', 'Գովազդ', 'विज्ञापन', 'Reklam',
    'آگهی', 'Reklāma', 'Reklaam', 'Διαφήμιση', 'מודעה', 'Hirdetés'
]


def generate_user_keys(cookies_disabled=False) -> dict:
    if cookies_disabled:
        return app.default_key_set

    # Generate/regenerate unique key per user
    return {
        'element_key': Fernet.generate_key(),
        'text_key': Fernet.generate_key()
    }


def valid_user_session(session):
    # Generate secret key for user if unavailable
    for value in REQUIRED_SESSION_VALUES:
        if value not in session:
            return False

    return True

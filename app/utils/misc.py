from cryptography.fernet import Fernet
from flask import current_app as app

SESSION_VALS = ['uuid', 'config', 'fernet_keys']


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
    for value in SESSION_VALS:
        if value not in session:
            return False

    return True

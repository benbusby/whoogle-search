from cryptography.fernet import Fernet
from flask import current_app as app

REQUIRED_SESSION_VALUES = ['uuid', 'config', 'key', 'auth']


def generate_key() -> bytes:
    """Generates a key for encrypting searches and element URLs

    Args:
        cookies_disabled: Flag for whether or not cookies are disabled by the
                          user. If so, the user can only use the default key
                          generated on app init for queries.

    Returns:
        str: A unique Fernet key

    """
    # Generate/regenerate unique key per user
    return Fernet.generate_key()


def valid_user_session(session: dict) -> bool:
    """Validates the current user session

    Args:
        session: The current Flask user session

    Returns:
        bool: True/False indicating that all required session values are
              available

    """
    # Generate secret key for user if unavailable
    for value in REQUIRED_SESSION_VALUES:
        if value not in session:
            return False

    return True

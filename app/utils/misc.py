from cryptography.fernet import Fernet

SESSION_VALS = ['uuid', 'config', 'keys']


def generate_user_keys():
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

from app import app
from app.utils.session_utils import generate_user_keys
import pytest


@pytest.fixture
def client():
    with app.test_client() as client:
        with client.session_transaction() as session:
            session['uuid'] = 'test'
            session['fernet_keys'] = generate_user_keys()
            session['config'] = {}
        yield client

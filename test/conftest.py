from app import app
from app.models.config import Config
from app.utils.session_utils import generate_user_keys
import pytest
import random

demo_config = {
    'near': random.choice(['Seattle', 'New York', 'San Francisco']),
    'dark_mode': str(random.getrandbits(1)),
    'nojs': str(random.getrandbits(1)),
    'lang_interface': random.choice(Config.LANGUAGES)['value'],
    'lang_search': random.choice(Config.LANGUAGES)['value'],
    'ctry': random.choice(Config.COUNTRIES)['value']
}


@pytest.fixture
def client():
    with app.test_client() as client:
        with client.session_transaction() as session:
            session['uuid'] = 'test'
            session['fernet_keys'] = generate_user_keys()
            session['config'] = {}
        yield client

from app.utils.misc import generate_user_keys, valid_user_session


def test_generate_user_keys():
    keys = generate_user_keys()
    assert 'text_key' in keys
    assert 'element_key' in keys
    assert keys['text_key'] not in keys['element_key']


def test_valid_session(client):
    with client.session_transaction() as session:
        assert not valid_user_session(session)

        session['uuid'] = 'test'
        session['keys'] = generate_user_keys()
        session['config'] = {}

        assert valid_user_session(session)


def test_request_key_generation(client):
    text_key = ''
    rv = client.get('/search?q=test+1')
    assert rv._status_code == 200

    with client.session_transaction() as session:
        assert valid_user_session(session)
        text_key = session['keys']['text_key']

    rv = client.get('/search?q=test+2')
    assert rv._status_code == 200

    with client.session_transaction() as session:
        assert valid_user_session(session)
        assert text_key not in session['keys']['text_key']

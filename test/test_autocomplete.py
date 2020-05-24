def test_autocomplete_get(client):
    rv = client.get('/autocomplete?q=green+eggs+and')
    assert rv._status_code == 200
    assert len(rv.data) >= 1
    assert b'green eggs and ham' in rv.data


def test_autocomplete_post(client):
    rv = client.post('/autocomplete', data=dict(q='the+cat+in+the'))
    assert rv._status_code == 200
    assert len(rv.data) >= 1
    assert b'the cat in the hat' in rv.data

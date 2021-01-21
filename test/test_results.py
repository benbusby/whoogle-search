from bs4 import BeautifulSoup
from app.filter import Filter
from app.utils.session_utils import generate_user_keys
from datetime import datetime
from dateutil.parser import *


def get_search_results(data):
    secret_key = generate_user_keys()
    soup = Filter(user_keys=secret_key).clean(
        BeautifulSoup(data, 'html.parser'))

    main_divs = soup.find('div', {'id': 'main'})
    assert len(main_divs) > 1

    result_divs = []
    for div in main_divs:
        # Result divs should only have 1 inner div
        if (len(list(div.children)) != 1
                or not div.findChild()
                or 'div' not in div.findChild().name):
            continue

        result_divs.append(div)

    return result_divs


def test_get_results(client):
    rv = client.get('/search?q=test')
    assert rv._status_code == 200

    # Depending on the search, there can be more
    # than 10 result divs
    assert len(get_search_results(rv.data)) >= 10
    assert len(get_search_results(rv.data)) <= 15


def test_post_results(client):
    rv = client.post('/search', data=dict(q='test'))
    assert rv._status_code == 200

    # Depending on the search, there can be more
    # than 10 result divs
    assert len(get_search_results(rv.data)) >= 10
    assert len(get_search_results(rv.data)) <= 15


# TODO: Unit test the site alt method instead -- the results returned
# are too unreliable for this test in particular.
# def test_site_alts(client):
    # rv = client.post('/search', data=dict(q='twitter official account'))
    # assert b'twitter.com/Twitter' in rv.data

    # client.post('/config', data=dict(alts=True))
    # assert json.loads(client.get('/config').data)['alts']

    # rv = client.post('/search', data=dict(q='twitter official account'))
    # assert b'twitter.com/Twitter' not in rv.data
    # assert b'nitter.net/Twitter' in rv.data


def test_recent_results(client):
    times = {
        'past year': 365,
        'past month': 31,
        'past week': 7
    }

    for time, num_days in times.items():
        rv = client.post('/search', data=dict(q='test :' + time))
        result_divs = get_search_results(rv.data)

        current_date = datetime.now()
        for div in [_ for _ in result_divs if _.find('span')]:
            date_span = div.find('span').decode_contents()
            if not date_span or len(date_span) > 15 or len(date_span) < 7:
                continue

            try:
                date = parse(date_span)
                # Date can have a little bit of wiggle room
                assert (current_date - date).days <= (num_days + 5)
            except ParserError:
                pass

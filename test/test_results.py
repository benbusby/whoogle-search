from bs4 import BeautifulSoup
from app.filter import Filter
import json
from datetime import datetime
from dateutil.parser import *
from test.conftest import client


def get_search_results(data):
    soup = Filter().clean(BeautifulSoup(data, 'html.parser'))

    main_divs = soup.find('div', {'id': 'main'})
    assert len(main_divs) > 1

    result_divs = []
    for div in main_divs:
        # Result divs should only have 1 inner div
        if len(list(div.children)) != 1 or not div.findChild() or 'div' not in div.findChild().name:
            continue

        result_divs.append(div)

    return result_divs


def test_search_results(client):
    rv = client.get('/search?q=test')
    assert rv._status_code == 200

    assert len(get_search_results(rv.data)) == 10


def test_recent_results(client):
    times = {
        'pastyear': 365,
        'pastmonth': 31,
        'pastweek': 7
    }

    for time, num_days in times.items():
        rv = client.get('/search?q=test%20%3A' + time)
        result_divs = get_search_results(rv.data)

        current_date = datetime.now()
        for div in result_divs:
            date_span = div.find('span').decode_contents()
            if not date_span or len(date_span) > 15:
                continue

            try:
                date = parse(date_span)
                assert (current_date - date).days < num_days
            except ParserError:
                assert ' ago' in date_span

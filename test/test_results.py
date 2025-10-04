from bs4 import BeautifulSoup
from app.filter import Filter
from app.models.config import Config
from app.models.endpoint import Endpoint
from app.utils import results
from app.utils import search as search_mod
from app.utils.session import generate_key
from datetime import datetime
from dateutil.parser import ParserError, parse
from urllib.parse import urlparse

from test.conftest import demo_config


def get_search_results(data):
    secret_key = generate_key()
    soup = Filter(user_key=secret_key, config=Config(**demo_config)).clean(
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


def test_get_results(client, monkeypatch):
    def fake_generate(self):
        # Build 10 results under #main, each with a single inner div
        items = []
        for i in range(10):
            items.append(f'<div><div><a href="https://example.com/{i}">Item {i}</a></div></div>')
        return f'<div id="main">{"".join(items)}</div>'

    monkeypatch.setattr(search_mod.Search, 'generate_response', fake_generate)

    rv = client.get(f'/{Endpoint.search}?q=test')
    assert rv._status_code == 200

    # Depending on the search, there can be more
    # than 10 result divs
    results_divs = get_search_results(rv.data)
    assert len(results_divs) >= 10
    assert len(results_divs) <= 15


def test_post_results(client):
    rv = client.post(f'/{Endpoint.search}', data=dict(q='test'))
    assert rv._status_code == 302


def test_translate_search(client):
    rv = client.get(f'/{Endpoint.search}?q=translate hola')
    assert rv._status_code == 200

    # Pretty weak test, but better than nothing
    str_data = str(rv.data)
    assert 'iframe' in str_data
    assert '/auto/en/ hola' in str_data


def test_block_results(client):
    rv = client.get(f'/{Endpoint.search}?q=pinterest')
    assert rv._status_code == 200

    has_pinterest = False
    for link in BeautifulSoup(rv.data, 'html.parser').find_all('a', href=True):
        if 'pinterest.com' in urlparse(link['href']).netloc:
            has_pinterest = True
            break

    assert has_pinterest

    demo_config['block'] = 'pinterest.com'
    rv = client.post(f'/{Endpoint.config}', data=demo_config)
    assert rv._status_code == 302

    rv = client.get(f'/{Endpoint.search}?q=pinterest')
    assert rv._status_code == 200

    for link in BeautifulSoup(rv.data, 'html.parser').find_all('a', href=True):
        result_site = urlparse(link['href']).netloc
        if not result_site:
            continue
        assert result_site not in 'pinterest.com'


def test_view_my_ip(client, monkeypatch):
    def fake_generate(self):
        # Minimal page; ip card is injected later by routes when widget == 'ip'
        return '<div id="main"></div>'

    monkeypatch.setattr(search_mod.Search, 'generate_response', fake_generate)

    rv = client.get(f'/{Endpoint.search}?q=my ip address')
    assert rv._status_code == 200

    # Pretty weak test, but better than nothing
    str_data = str(rv.data)
    assert 'Your public IP address' in str_data
    assert '127.0.0.1' in str_data


def test_recent_results(client, monkeypatch):
    def fake_generate(self):
        # Create results with a span containing today's date so it passes all windows
        today = datetime.now().strftime('%b %d, %Y')
        items = []
        for i in range(5):
            items.append(f'<div><div><span>{today}</span></div></div>')
        return f'<div id="main">{"".join(items)}</div>'

    monkeypatch.setattr(search_mod.Search, 'generate_response', fake_generate)

    times = {
        'tbs=qdr:y': 365,
        'tbs=qdr:m': 31,
        'tbs=qdr:w': 7
    }

    for time, num_days in times.items():
        rv = client.get(f'/{Endpoint.search}?q=test&' + time)
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


def test_leading_slash_search(client):
    # Ensure searches with a leading slash are interpreted
    # correctly as queries and not endpoints
    q = '/test'
    rv = client.get(f'/{Endpoint.search}?q={q}')
    assert rv._status_code == 200

    soup = Filter(
        user_key=generate_key(),
        config=Config(**demo_config),
        query=q
    ).clean(BeautifulSoup(rv.data, 'html.parser'))

    for link in soup.find_all('a', href=True):
        if 'start=' not in link['href']:
            continue

        assert link['href'].startswith(f'{Endpoint.search}')


def test_site_alt_prefix_skip():
    # Ensure prefixes are skipped correctly for site alts

    # default silte_alts (farside.link)
    assert results.get_site_alt(link = 'https://www.reddit.com') == 'https://farside.link/libreddit'
    assert results.get_site_alt(link = 'https://www.twitter.com') == 'https://farside.link/nitter'
    assert results.get_site_alt(link = 'https://www.youtube.com') == 'https://farside.link/invidious'

    test_site_alts = {
    'reddit.com': 'reddit.endswithmobile.domain',
    'twitter.com': 'https://twitter.endswithm.domain',
    'youtube.com': 'http://yt.endswithwww.domain',
    }
    # Domains with part of SKIP_PREFIX in them
    assert results.get_site_alt(link = 'https://www.reddit.com', site_alts = test_site_alts) == 'https://reddit.endswithmobile.domain'
    assert results.get_site_alt(link = 'https://www.twitter.com', site_alts = test_site_alts) == 'https://twitter.endswithm.domain'
    assert results.get_site_alt(link = 'https://www.youtube.com', site_alts = test_site_alts) == 'http://yt.endswithwww.domain'

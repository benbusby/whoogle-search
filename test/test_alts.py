import copy
import os

from bs4 import BeautifulSoup

from app import app
from app.filter import Filter
from app.models.config import Config
from app.utils.session import generate_key
from app.utils import results as results_mod


def build_soup(html: str):
    return BeautifulSoup(html, 'html.parser')


def make_filter(soup: BeautifulSoup):
    secret_key = generate_key()
    with app.app_context():
        cfg = Config(**{'alts': True})
    f = Filter(user_key=secret_key, config=cfg)
    f.soup = soup
    return f


def test_no_duplicate_alt_prefix_reddit(monkeypatch):
    original_site_alts = copy.deepcopy(results_mod.SITE_ALTS)
    try:
        # Simulate user setting alt to old.reddit.com
        monkeypatch.setitem(results_mod.SITE_ALTS, 'reddit.com', 'old.reddit.com')

        html = '''
        <div id="main">
          <a href="https://www.reddit.com/r/whoogle">www.reddit.com</a>
          <div>www.reddit.com</div>
          <div>old.reddit.com</div>
        </div>
        '''
        soup = build_soup(html)
        f = make_filter(soup)
        f.site_alt_swap()

        # Href replaced once
        a = soup.find('a')
        assert a['href'].startswith('https://old.reddit.com')

        # Bare domain replaced, but already-alt text stays unchanged (no old.old...)
        divs = [d.get_text() for d in soup.find_all('div') if d.get_text().strip()]
        assert 'old.reddit.com' in divs
        assert 'old.old.reddit.com' not in ''.join(divs)
    finally:
        results_mod.SITE_ALTS.clear()
        results_mod.SITE_ALTS.update(original_site_alts)


def test_wikipedia_simple_no_lang_param(monkeypatch):
    original_site_alts = copy.deepcopy(results_mod.SITE_ALTS)
    try:
        monkeypatch.setitem(results_mod.SITE_ALTS, 'wikipedia.org', 'https://wikiless.example')

        html = '''
        <div id="main">
          <a href="https://simple.wikipedia.org/wiki/Whoogle">https://simple.wikipedia.org/wiki/Whoogle</a>
          <div>simple.wikipedia.org</div>
        </div>
        '''
        soup = build_soup(html)
        f = make_filter(soup)
        f.site_alt_swap()

        a = soup.find('a')
        # Should be rewritten to the alt host, without ?lang
        assert a['href'].startswith('https://wikiless.example')
        assert '?lang=' not in a['href']

        # Description host replaced once
        text = soup.find('div').get_text()
        assert 'wikiless.example' in text
        assert 'simple.wikipedia.org' not in text
    finally:
        results_mod.SITE_ALTS.clear()
        results_mod.SITE_ALTS.update(original_site_alts)


def test_single_pass_description_replacement(monkeypatch):
    original_site_alts = copy.deepcopy(results_mod.SITE_ALTS)
    try:
        monkeypatch.setitem(results_mod.SITE_ALTS, 'twitter.com', 'https://nitter.example')

        html = '''
        <div id="main">
          <a href="https://twitter.com/whoogle">https://twitter.com/whoogle</a>
          <div>https://www.twitter.com</div>
        </div>
        '''
        soup = build_soup(html)
        f = make_filter(soup)
        f.site_alt_swap()

        a = soup.find('a')
        assert a['href'].startswith('https://nitter.example')

        # Ensure description got host swapped once, no double scheme or duplication
        main_div = soup.find('div', id='main')
        # The description div is the first inner div under #main in this fixture
        text = main_div.find_all('div')[0].get_text().strip()
        assert text.startswith('https://nitter.example')
        assert 'https://https://' not in text
        assert 'nitter.examplenitter.example' not in text
    finally:
        results_mod.SITE_ALTS.clear()
        results_mod.SITE_ALTS.update(original_site_alts)



from app.filter import Filter, get_first_link
from app.utils.session import generate_user_keys
from app.request import gen_query
from bs4 import BeautifulSoup as bsoup
from cryptography.fernet import Fernet, InvalidToken
from flask import g
from typing import Any, Tuple
import os

TOR_BANNER = '<hr><h1 style="text-align: center">You are using Tor</h1><hr>'
CAPTCHA = 'div class="g-recaptcha"'


def needs_https(url: str) -> bool:
    """Checks if the current instance needs to be upgraded to HTTPS

    Note that all Heroku instances are available by default over HTTPS, but
    do not automatically set up a redirect when visited over HTTP.

    Args:
        url: The instance url

    Returns:
        bool: True/False representing the need to upgrade

    """
    https_only = os.getenv('HTTPS_ONLY', False)
    is_heroku = url.endswith('.herokuapp.com')
    is_http = url.startswith('http://')

    return (is_heroku and is_http) or (https_only and is_http)


def has_captcha(site_contents: str) -> bool:
    return CAPTCHA in site_contents


class Search:
    """Search query preprocessor - used before submitting the query or
    redirecting to another site

    Attributes:
        request: the incoming flask request
        config: the current user config settings
        session: the flask user session
    """
    def __init__(self, request, config, session, cookies_disabled=False):
        method = request.method
        self.request_params = request.args if method == 'GET' else request.form
        self.user_agent = request.headers.get('User-Agent')
        self.feeling_lucky = False
        self.config = config
        self.session = session
        self.query = ''
        self.cookies_disabled = cookies_disabled
        self.search_type = self.request_params.get(
            'tbm') if 'tbm' in self.request_params else ''

    def __getitem__(self, name) -> Any:
        return getattr(self, name)

    def __setitem__(self, name, value) -> None:
        return setattr(self, name, value)

    def __delitem__(self, name) -> None:
        return delattr(self, name)

    def __contains__(self, name) -> bool:
        return hasattr(self, name)

    def new_search_query(self) -> str:
        """Parses a plaintext query into a valid string for submission

        Also decrypts the query string, if encrypted (in the case of
        paginated results).

        Returns:
            str: A valid query string

        """
        # Generate a new element key each time a new search is performed
        self.session['fernet_keys']['element_key'] = generate_user_keys(
            cookies_disabled=self.cookies_disabled)['element_key']

        q = self.request_params.get('q')

        if q is None or len(q) == 0:
            return ''
        else:
            # Attempt to decrypt if this is an internal link
            try:
                q = Fernet(
                    self.session['fernet_keys']['text_key']
                ).decrypt(q.encode()).decode()
            except InvalidToken:
                pass

        # Reset text key
        self.session['fernet_keys']['text_key'] = generate_user_keys(
            cookies_disabled=self.cookies_disabled)['text_key']

        # Strip leading '! ' for "feeling lucky" queries
        self.feeling_lucky = q.startswith('! ')
        self.query = q[2:] if self.feeling_lucky else q
        return self.query

    def generate_response(self) -> Tuple[Any, int]:
        """Generates a response for the user's query

        Returns:
            Tuple[Any, int]: A tuple in the format (response, # of elements)
                             For example, in the case of a "feeling lucky"
                             search, the response is a result URL, with no
                             encrypted elements to account for. Otherwise, the
                             response is a BeautifulSoup response body, with
                             N encrypted elements to track before key regen.

        """
        mobile = 'Android' in self.user_agent or 'iPhone' in self.user_agent

        content_filter = Filter(
            self.session['fernet_keys'],
            mobile=mobile,
            config=self.config)
        full_query = gen_query(
            self.query,
            self.request_params,
            self.config,
            content_filter.near)
        get_body = g.user_request.send(query=full_query)

        # Produce cleanable html soup from response
        html_soup = bsoup(content_filter.reskin(get_body.text), 'html.parser')
        html_soup.insert(
            0,
            bsoup(TOR_BANNER, 'html.parser')
            if g.user_request.tor_valid else bsoup('', 'html.parser'))

        if self.feeling_lucky:
            return get_first_link(html_soup), 0
        else:
            formatted_results = content_filter.clean(html_soup)

            # Append user config to all search links, if available
            param_str = ''.join('&{}={}'.format(k, v)
                                for k, v in
                                self.request_params.to_dict(flat=True).items()
                                if self.config.is_safe_key(k))
            for link in formatted_results.find_all('a', href=True):
                if 'search?' not in link['href'] or link['href'].index(
                        'search?') > 1:
                    continue
                link['href'] += param_str

            return formatted_results, content_filter.elements

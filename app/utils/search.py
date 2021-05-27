import os
from typing import Any

from bs4 import BeautifulSoup as bsoup
from cryptography.fernet import Fernet, InvalidToken
from flask import g

from app.filter import Filter, get_first_link
from app.request import gen_query

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
    https_only = bool(os.getenv('HTTPS_ONLY', 0))
    is_heroku = url.endswith('.herokuapp.com')
    is_http = url.startswith('http://')

    return (is_heroku and is_http) or (https_only and is_http)


def has_captcha(results: str) -> bool:
    """Checks to see if the search results are blocked by a captcha

    Args:
        results: The search page html as a string

    Returns:
        bool: True/False indicating if a captcha element was found

    """
    return CAPTCHA in results


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
        q = self.request_params.get('q')

        if q is None or len(q) == 0:
            return ''
        else:
            # Attempt to decrypt if this is an internal link
            try:
                q = Fernet(self.session['key']).decrypt(q.encode()).decode()
            except InvalidToken:
                pass

        # Strip leading '! ' for "feeling lucky" queries
        self.feeling_lucky = q.startswith('! ')
        self.query = q[2:] if self.feeling_lucky else q
        return self.query

    def generate_response(self) -> str:
        """Generates a response for the user's query

        Returns:
            str: A string response to the search query, in the form of a URL
                 or string representation of HTML content.

        """
        mobile = 'Android' in self.user_agent or 'iPhone' in self.user_agent

        content_filter = Filter(self.session['key'],
                                mobile=mobile,
                                config=self.config)
        full_query = gen_query(self.query,
                               self.request_params,
                               self.config,
                               content_filter.near)

        # force mobile search when view image is true and
        # the request is not already made by a mobile
        view_image = ('tbm=isch' in full_query
                      and self.config.view_image
                      and not g.user_request.mobile)

        get_body = g.user_request.send(query=full_query,
                                       force_mobile=view_image)

        # Produce cleanable html soup from response
        html_soup = bsoup(content_filter.reskin(get_body.text), 'html.parser')

        # Replace current soup if view_image is active
        if view_image:
            html_soup = content_filter.view_image(html_soup)

        # Indicate whether or not a Tor connection is active
        tor_banner = bsoup('', 'html.parser')
        if g.user_request.tor_valid:
            tor_banner = bsoup(TOR_BANNER, 'html.parser')
        html_soup.insert(0, tor_banner)

        if self.feeling_lucky:
            return get_first_link(html_soup)
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

            return str(formatted_results)

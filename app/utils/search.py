import os
import re
from typing import Any
from app.filter import Filter
from app.request import gen_query
from app.utils.misc import get_proxy_host_url
from app.utils.results import get_first_link
from bs4 import BeautifulSoup as bsoup
from cryptography.fernet import Fernet, InvalidToken
from flask import g

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
        session_key: the flask user fernet key
    """
    def __init__(self, request, config, session_key, cookies_disabled=False):
        method = request.method
        self.request = request
        self.request_params = request.args if method == 'GET' else request.form
        self.user_agent = request.headers.get('User-Agent')
        self.feeling_lucky = False
        self.config = config
        self.session_key = session_key
        self.query = ''
        self.widget = ''
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
                q = Fernet(self.session_key).decrypt(q.encode()).decode()
            except InvalidToken:
                pass

        # Strip leading '! ' for "feeling lucky" queries
        self.feeling_lucky = q.startswith('! ')
        self.query = q[2:] if self.feeling_lucky else q
        # Check for possible widgets
        self.widget = "ip" if re.search("([^a-z0-9]|^)my *[^a-z0-9] *(ip|internet protocol)" +
                        "($|( *[^a-z0-9] *(((addres|address|adres|" +
                        "adress)|a)? *$)))", self.query.lower()) else self.widget
        self.widget = 'calculator' if re.search("calculator|calc|calclator|math", self.query.lower()) else self.widget
        return self.query

    def generate_response(self) -> str:
        """Generates a response for the user's query

        Returns:
            str: A string response to the search query, in the form of a URL
                 or string representation of HTML content.

        """
        mobile = 'Android' in self.user_agent or 'iPhone' in self.user_agent
        # reconstruct url if X-Forwarded-Host header present
        root_url = get_proxy_host_url(
            self.request,
            self.request.url_root,
            root=True)

        content_filter = Filter(self.session_key,
                                root_url=root_url,
                                mobile=mobile,
                                config=self.config,
                                query=self.query)
        full_query = gen_query(self.query,
                               self.request_params,
                               self.config)
        self.full_query = full_query

        # force mobile search when view image is true and
        # the request is not already made by a mobile
        view_image = ('tbm=isch' in full_query
                      and self.config.view_image
                      and not g.user_request.mobile)

        get_body = g.user_request.send(query=full_query,
                                       force_mobile=view_image,
                                       user_agent=self.user_agent)

        # Produce cleanable html soup from response
        get_body_safed = get_body.text.replace("&lt;","andlt;").replace("&gt;","andgt;")
        html_soup = bsoup(get_body_safed, 'html.parser')

        # Replace current soup if view_image is active
        if view_image:
            html_soup = content_filter.view_image(html_soup)

        # Indicate whether or not a Tor connection is active
        if g.user_request.tor_valid:
            html_soup.insert(0, bsoup(TOR_BANNER, 'html.parser'))

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
                link['rel'] = "nofollow noopener noreferrer"
                if 'search?' not in link['href'] or link['href'].index(
                        'search?') > 1:
                    continue
                link['href'] += param_str

            return str(formatted_results)


from app.filter import Filter, get_first_link
from app.utils.session_utils import generate_user_keys
from app.request import gen_query
from bs4 import BeautifulSoup as bsoup
from cryptography.fernet import Fernet, InvalidToken
from flask import g
from typing import Any, Tuple
import os

TOR_BANNER = '<hr><h1 style="text-align: center">You are using Tor</h1><hr>'


def needs_https(url: str) -> bool:
    https_only = os.getenv('HTTPS_ONLY', False)
    is_heroku = url.endswith('.herokuapp.com')
    is_http = url.startswith('http://')

    return (is_heroku and is_http) or (https_only and is_http)


class RoutingUtils:
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

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        return setattr(self, name, value)

    def __delitem__(self, name):
        return delattr(self, name)

    def __contains__(self, name):
        return hasattr(self, name)

    def new_search_query(self) -> str:
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

    def bang_operator(self, bangs_dict: dict) -> str:
        for operator in bangs_dict.keys():
            if self.query.split(' ')[0] != operator:
                continue

            return bangs_dict[operator]['url'].format(
                self.query.replace(operator, '').strip())
        return ''

    def generate_response(self) -> Tuple[Any, int]:
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
            return get_first_link(html_soup), 1
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

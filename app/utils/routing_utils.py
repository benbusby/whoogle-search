from app.filter import Filter, get_first_link
from app.utils.session_utils import generate_user_keys
from app.request import gen_query
from bs4 import BeautifulSoup
from cryptography.fernet import Fernet, InvalidToken
from flask import g
from typing import Any, Tuple


class RoutingUtils:
    def __init__(self, request, config, session, cookies_disabled=False):
        self.request_params = request.args if request.method == 'GET' else request.form
        self.user_agent = request.headers.get('User-Agent')
        self.feeling_lucky = False
        self.config = config
        self.session = session
        self.query = ''
        self.cookies_disabled = cookies_disabled
        self.search_type = self.request_params.get('tbm') if 'tbm' in self.request_params else ''

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
                q = Fernet(self.session['fernet_keys']['text_key']).decrypt(q.encode()).decode()
            except InvalidToken:
                pass

        # Reset text key
        self.session['fernet_keys']['text_key'] = generate_user_keys(
            cookies_disabled=self.cookies_disabled)['text_key']

        # Format depending on whether or not the query is a "feeling lucky" query
        self.feeling_lucky = q.startswith('! ')
        self.query = q[2:] if self.feeling_lucky else q
        return self.query

    def generate_response(self) -> Tuple[Any, int]:
        mobile = 'Android' in self.user_agent or 'iPhone' in self.user_agent

        content_filter = Filter(self.session['fernet_keys'], mobile=mobile, config=self.config)
        full_query = gen_query(self.query, self.request_params, self.config, content_filter.near)
        get_body = g.user_request.send(query=full_query).text

        # Produce cleanable html soup from response
        html_soup = BeautifulSoup(content_filter.reskin(get_body), 'html.parser')

        if self.feeling_lucky:
            return get_first_link(html_soup), 1
        else:
            formatted_results = content_filter.clean(html_soup)
            return formatted_results, content_filter.elements

from app.models.config import Config
import xml.etree.ElementTree as ET
import random
import requests
from requests import Response, ConnectionError
import urllib.parse as urlparse
import os
from stem import Signal, SocketError
from stem.control import Controller

SEARCH_URL = 'https://www.google.com/search?gbv=1&q='
AUTOCOMPLETE_URL = ('https://suggestqueries.google.com/'
                    'complete/search?client=toolbar&')

MOBILE_UA = '{}/5.0 (Android 0; Mobile; rv:54.0) Gecko/54.0 {}/59.0'
DESKTOP_UA = '{}/5.0 (X11; {} x86_64; rv:75.0) Gecko/20100101 {}/75.0'

# Valid query params
VALID_PARAMS = ['tbs', 'tbm', 'start', 'near', 'source', 'nfpr']


class TorError(Exception):
    """Exception raised for errors in Tor requests.

    Attributes:
        message -- a message describing the error that occurred
        disable -- optionally disables Tor in the user config (note:
            this should only happen if the connection has been dropped
            altogether).
    """

    def __init__(self, message, disable=False):
        self.message = message
        self.disable = disable
        super().__init__(self.message)


def send_tor_signal(signal: Signal) -> bool:
    try:
        with Controller.from_port(port=9051) as c:
            c.authenticate()
            c.signal(signal)
            os.environ['TOR_AVAILABLE'] = '1'
            return True
    except (SocketError, ConnectionRefusedError, ConnectionError):
        os.environ['TOR_AVAILABLE'] = '0'

    return False


def gen_user_agent(is_mobile) -> str:
    mozilla = random.choice(['Moo', 'Woah', 'Bro', 'Slow']) + 'zilla'
    firefox = random.choice(['Choir', 'Squier', 'Higher', 'Wire']) + 'fox'
    linux = random.choice(['Win', 'Sin', 'Gin', 'Fin', 'Kin']) + 'ux'

    if is_mobile:
        return MOBILE_UA.format(mozilla, firefox)

    return DESKTOP_UA.format(mozilla, linux, firefox)


def gen_query(query, args, config, near_city=None) -> str:
    param_dict = {key: '' for key in VALID_PARAMS}

    # Use :past(hour/day/week/month/year) if available
    # example search "new restaurants :past month"
    sub_lang = ''
    if ':past' in query and 'tbs' not in args:
        time_range = str.strip(query.split(':past', 1)[-1])
        param_dict['tbs'] = '&tbs=' + ('qdr:' + str.lower(time_range[0]))
    elif 'tbs' in args:
        result_tbs = args.get('tbs')
        param_dict['tbs'] = '&tbs=' + result_tbs

        # Occasionally the 'tbs' param provided by google also contains a
        # field for 'lr', but formatted strangely. This is a rough solution
        # for this.
        #
        # Example:
        # &tbs=qdr:h,lr:lang_1pl
        # -- the lr param needs to be extracted and remove the leading '1'
        sub_lang = [_ for _ in result_tbs.split(',') if 'lr:' in _]
        sub_lang = sub_lang[0][sub_lang[0].find('lr:') +
                               3:len(sub_lang[0])] if len(sub_lang) > 0 else ''

    # Ensure search query is parsable
    query = urlparse.quote(query)

    # Pass along type of results (news, images, books, etc)
    if 'tbm' in args:
        param_dict['tbm'] = '&tbm=' + args.get('tbm')

    # Get results page start value (10 per page, ie page 2 start val = 20)
    if 'start' in args:
        param_dict['start'] = '&start=' + args.get('start')

    # Search for results near a particular city, if available
    if near_city:
        param_dict['near'] = '&near=' + urlparse.quote(near_city)

    # Set language for results (lr) if source isn't set, otherwise use the
    # result language param provided in the results
    if 'source' in args:
        param_dict['source'] = '&source=' + args.get('source')
        param_dict['lr'] = ('&lr=' + ''.join(
            [_ for _ in sub_lang if not _.isdigit()]
        )) if sub_lang else ''
    else:
        param_dict['lr'] = (
                '&lr=' + config.lang_search
        ) if config.lang_search else ''

    # 'nfpr' defines the exclusion of results from an auto-corrected query
    if 'nfpr' in args:
        param_dict['nfpr'] = '&nfpr=' + args.get('nfpr')

    param_dict['cr'] = ('&cr=' + config.ctry) if config.ctry else ''
    param_dict['hl'] = (
            '&hl=' + config.lang_interface.replace('lang_', '')
    ) if config.lang_interface else ''
    param_dict['safe'] = '&safe=' + ('active' if config.safe else 'off')

    for val in param_dict.values():
        if not val:
            continue
        query += val

    return query


class Request:
    """Class used for handling all outbound requests, including search queries,
    search suggestions, and loading of external content (images, audio, etc).

    Attributes:
        normal_ua -- the user's current user agent
        root_path -- the root path of the whoogle instance
        config -- the user's current whoogle configuration
    """

    def __init__(self, normal_ua, root_path, config: Config):
        # Send heartbeat to Tor, used in determining if the user can or cannot
        # enable Tor for future requests
        send_tor_signal(Signal.HEARTBEAT)

        self.language = config.lang_search
        self.mobile = 'Android' in normal_ua or 'iPhone' in normal_ua
        self.modified_user_agent = gen_user_agent(self.mobile)

        # Set up proxy, if previously configured
        if os.environ.get('WHOOGLE_PROXY_LOC'):
            auth_str = ''
            if os.environ.get('WHOOGLE_PROXY_USER'):
                auth_str = os.environ.get('WHOOGLE_PROXY_USER') + \
                           ':' + os.environ.get('WHOOGLE_PROXY_PASS')
            self.proxies = {
                'http': os.environ.get('WHOOGLE_PROXY_TYPE') + '://' +
                auth_str + '@' + os.environ.get('WHOOGLE_PROXY_LOC'),
            }
            self.proxies['https'] = self.proxies['http'].replace('http',
                                                                 'https')
        else:
            self.proxies = {
                'http': 'socks5://127.0.0.1:9050',
                'https': 'socks5://127.0.0.1:9050'
            } if config.tor else {}
        self.tor = config.tor
        self.tor_valid = False
        self.root_path = root_path

    def __getitem__(self, name):
        return getattr(self, name)

    def autocomplete(self, query) -> list:
        """Sends a query to Google's search suggestion service

        Args:
            query: The in-progress query to send

        Returns:
            list: The list of matches for possible search suggestions

        """
        ac_query = dict(hl=self.language, q=query)
        response = self.send(base_url=AUTOCOMPLETE_URL,
                             query=urlparse.urlencode(ac_query)).text

        if not response:
            return []

        root = ET.fromstring(response)
        return [_.attrib['data'] for _ in
                root.findall('.//suggestion/[@data]')]

    def send(self, base_url=SEARCH_URL, query='', attempt=0) -> Response:
        """Sends an outbound request to a URL. Optionally sends the request
        using Tor, if enabled by the user.

        Args:
            base_url: The URL to use in the request
            query: The optional query string for the request
            attempt: The number of attempts made for the request
                (used for cycling through Tor identities, if enabled)

        Returns:
            Response: The Response object returned by the requests call

        """
        headers = {
            'User-Agent': self.modified_user_agent
        }

        # FIXME: Should investigate this further to ensure the consent
        # view is suppressed correctly
        cookies = {
            'CONSENT': 'PENDING+999'
        }

        # Validate Tor conn and request new identity if the last one failed
        if self.tor and not send_tor_signal(
                Signal.NEWNYM if attempt > 0 else Signal.HEARTBEAT):
            raise TorError(
                "Tor was previously enabled, but the connection has been "
                "dropped. Please check your Tor configuration and try again.",
                disable=True)

        # Make sure that the tor connection is valid, if enabled
        if self.tor:
            tor_check = requests.get('https://check.torproject.org/',
                                     proxies=self.proxies, headers=headers)
            self.tor_valid = 'Congratulations' in tor_check.text

            if not self.tor_valid:
                raise TorError(
                    "Tor connection succeeded, but the connection could not "
                    "be validated by torproject.org",
                    disable=True)

        response = requests.get(
            base_url + query,
            proxies=self.proxies,
            headers=headers,
            cookies=cookies)

        # Retry query with new identity if using Tor (max 10 attempts)
        if 'form id="captcha-form"' in response.text and self.tor:
            attempt += 1
            if attempt > 10:
                raise TorError("Tor query failed -- max attempts exceeded 10")
            return self.send(base_url, query, attempt)

        return response

from app.models.config import Config
from app.utils.misc import read_config_bool
from datetime import datetime
from defusedxml import ElementTree as ET
import random
import requests
from requests import Response, ConnectionError
import urllib.parse as urlparse
import os
from stem import Signal, SocketError
from stem.connection import AuthenticationFailure
from stem.control import Controller
from stem.connection import authenticate_cookie, authenticate_password

MAPS_URL = 'https://maps.google.com/maps'
AUTOCOMPLETE_URL = ('https://suggestqueries.google.com/'
                    'complete/search?client=toolbar&')

MOBILE_UA = '{}/5.0 (Android 0; Mobile; rv:54.0) Gecko/54.0 {}/59.0'
DESKTOP_UA = '{}/5.0 (X11; {} x86_64; rv:75.0) Gecko/20100101 {}/75.0'

# Valid query params
VALID_PARAMS = ['tbs', 'tbm', 'start', 'near', 'source', 'nfpr']


class TorError(Exception):
    """Exception raised for errors in Tor requests.

    Attributes:
        message: a message describing the error that occurred
        disable: optionally disables Tor in the user config (note:
            this should only happen if the connection has been dropped
            altogether).
    """

    def __init__(self, message, disable=False) -> None:
        self.message = message
        self.disable = disable
        super().__init__(message)


def send_tor_signal(signal: Signal) -> bool:
    use_pass = read_config_bool('WHOOGLE_TOR_USE_PASS')

    confloc = './misc/tor/control.conf'
    # Check that the custom location of conf is real.
    temp = os.getenv('WHOOGLE_TOR_CONF', '')
    if os.path.isfile(temp):
        confloc = temp

    # Attempt to authenticate and send signal.
    try:
        with Controller.from_port(port=9051) as c:
            if use_pass:
                with open(confloc, "r") as conf:
                    # Scan for the last line of the file.
                    for line in conf:
                        pass
                    secret = line.strip('\n')
                authenticate_password(c, password=secret)
            else:
                cookie_path = '/var/lib/tor/control_auth_cookie'
                authenticate_cookie(c, cookie_path=cookie_path)
            c.signal(signal)
            os.environ['TOR_AVAILABLE'] = '1'
            return True
    except (SocketError, AuthenticationFailure,
            ConnectionRefusedError, ConnectionError):
        # TODO: Handle Tor authentication (password and cookie)
        os.environ['TOR_AVAILABLE'] = '0'

    return False


def gen_user_agent(is_mobile) -> str:
    firefox = random.choice(['Choir', 'Squier', 'Higher', 'Wire']) + 'fox'
    linux = random.choice(['Win', 'Sin', 'Gin', 'Fin', 'Kin']) + 'ux'

    if is_mobile:
        return MOBILE_UA.format("Mozilla", firefox)

    return DESKTOP_UA.format("Mozilla", linux, firefox)


def gen_query(query, args, config) -> str:
    param_dict = {key: '' for key in VALID_PARAMS}

    # Use :past(hour/day/week/month/year) if available
    # example search "new restaurants :past month"
    lang = ''
    if ':past' in query and 'tbs' not in args:
        time_range = str.strip(query.split(':past', 1)[-1])
        param_dict['tbs'] = '&tbs=' + ('qdr:' + str.lower(time_range[0]))
    elif 'tbs' in args or 'tbs' in config:
        result_tbs = args.get('tbs') if 'tbs' in args else config['tbs']
        param_dict['tbs'] = '&tbs=' + result_tbs

        # Occasionally the 'tbs' param provided by google also contains a
        # field for 'lr', but formatted strangely. This is a rough solution
        # for this.
        #
        # Example:
        # &tbs=qdr:h,lr:lang_1pl
        # -- the lr param needs to be extracted and remove the leading '1'
        result_params = [_ for _ in result_tbs.split(',') if 'lr:' in _]
        if len(result_params) > 0:
            result_param = result_params[0]
            lang = result_param[result_param.find('lr:') + 3:len(result_param)]

    # Ensure search query is parsable
    query = urlparse.quote(query)

    # Pass along type of results (news, images, books, etc)
    if 'tbm' in args:
        param_dict['tbm'] = '&tbm=' + args.get('tbm')

    # Get results page start value (10 per page, ie page 2 start val = 20)
    if 'start' in args:
        param_dict['start'] = '&start=' + args.get('start')

    # Search for results near a particular city, if available
    if config.near:
        param_dict['near'] = '&near=' + urlparse.quote(config.near)

    # Set language for results (lr) if source isn't set, otherwise use the
    # result language param provided in the results
    if 'source' in args:
        param_dict['source'] = '&source=' + args.get('source')
        param_dict['lr'] = ('&lr=' + ''.join(
            [_ for _ in lang if not _.isdigit()]
        )) if lang else ''
    else:
        param_dict['lr'] = (
            '&lr=' + config.lang_search
        ) if config.lang_search else ''

    # 'nfpr' defines the exclusion of results from an auto-corrected query
    if 'nfpr' in args:
        param_dict['nfpr'] = '&nfpr=' + args.get('nfpr')

    # 'chips' is used in image tabs to pass the optional 'filter' to add to the
    # given search term
    if 'chips' in args:
        param_dict['chips'] = '&chips=' + args.get('chips')

    param_dict['gl'] = (
        '&gl=' + config.country
    ) if config.country else ''
    param_dict['hl'] = (
        '&hl=' + config.lang_interface.replace('lang_', '')
    ) if config.lang_interface else ''
    param_dict['safe'] = '&safe=' + ('active' if config.safe else 'off')

    # Block all sites specified in the user config
    unquoted_query = urlparse.unquote(query)
    for blocked_site in config.block.replace(' ', '').split(','):
        if not blocked_site:
            continue
        block = (' -site:' + blocked_site)
        query += block if block not in unquoted_query else ''

    for val in param_dict.values():
        if not val:
            continue
        query += val

    return query


class Request:
    """Class used for handling all outbound requests, including search queries,
    search suggestions, and loading of external content (images, audio, etc).

    Attributes:
        normal_ua: the user's current user agent
        root_path: the root path of the whoogle instance
        config: the user's current whoogle configuration
    """

    def __init__(self, normal_ua, root_path, config: Config):
        self.search_url = 'https://www.google.com/search?gbv=1&num=' + str(
            os.getenv('WHOOGLE_RESULTS_PER_PAGE', 10)) + '&q='
        # Send heartbeat to Tor, used in determining if the user can or cannot
        # enable Tor for future requests
        send_tor_signal(Signal.HEARTBEAT)

        self.language = (
            config.lang_search if config.lang_search else ''
        )

        self.country = config.country if config.country else ''

        # For setting Accept-language Header
        self.lang_interface = ''
        if config.accept_language:
            self.lang_interface = config.lang_interface

        self.mobile = bool(normal_ua) and ('Android' in normal_ua
                                           or 'iPhone' in normal_ua)
        self.modified_user_agent = gen_user_agent(self.mobile)
        if not self.mobile:
            self.modified_user_agent_mobile = gen_user_agent(True)

        # Set up proxy, if previously configured
        proxy_path = os.environ.get('WHOOGLE_PROXY_LOC', '')
        if proxy_path:
            proxy_type = os.environ.get('WHOOGLE_PROXY_TYPE', '')
            proxy_user = os.environ.get('WHOOGLE_PROXY_USER', '')
            proxy_pass = os.environ.get('WHOOGLE_PROXY_PASS', '')
            auth_str = ''
            if proxy_user:
                auth_str = f'{proxy_user}:{proxy_pass}@'

            proxy_str = f'{proxy_type}://{auth_str}{proxy_path}'
            self.proxies = {
                'https': proxy_str,
                'http': proxy_str
            }
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
        ac_query = dict(q=query)
        if self.language:
            ac_query['lr'] = self.language
        if self.country:
            ac_query['gl'] = self.country
        if self.lang_interface:
            ac_query['hl'] = self.lang_interface

        response = self.send(base_url=AUTOCOMPLETE_URL,
                             query=urlparse.urlencode(ac_query)).text

        if not response:
            return []

        try:
            root = ET.fromstring(response)
            return [_.attrib['data'] for _ in
                    root.findall('.//suggestion/[@data]')]
        except ET.ParseError:
            # Malformed XML response
            return []

    def send(self, base_url='', query='', attempt=0,
             force_mobile=False) -> Response:
        """Sends an outbound request to a URL. Optionally sends the request
        using Tor, if enabled by the user.

        Args:
            base_url: The URL to use in the request
            query: The optional query string for the request
            attempt: The number of attempts made for the request
                (used for cycling through Tor identities, if enabled)
            force_mobile: Optional flag to enable a mobile user agent
                (used for fetching full size images in search results)

        Returns:
            Response: The Response object returned by the requests call

        """
        if force_mobile and not self.mobile:
            modified_user_agent = self.modified_user_agent_mobile
        else:
            modified_user_agent = self.modified_user_agent

        headers = {
            'User-Agent': modified_user_agent
        }

        # Adding the Accept-Language to the Header if possible
        if self.lang_interface:
            headers.update({'Accept-Language':
                            self.lang_interface.replace('lang_', '')
                            + ';q=1.0'})

        # view is suppressed correctly
        now = datetime.now()
        cookies = {
            'CONSENT': 'YES+cb.{:d}{:02d}{:02d}-17-p0.de+F+678'.format(
                now.year, now.month, now.day
            )
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
            try:
                tor_check = requests.get('https://check.torproject.org/',
                                         proxies=self.proxies, headers=headers)
                self.tor_valid = 'Congratulations' in tor_check.text

                if not self.tor_valid:
                    raise TorError(
                        "Tor connection succeeded, but the connection could "
                        "not be validated by torproject.org",
                        disable=True)
            except ConnectionError:
                raise TorError(
                    "Error raised during Tor connection validation",
                    disable=True)

        response = requests.get(
            (base_url or self.search_url) + query,
            proxies=self.proxies,
            headers=headers,
            cookies=cookies)

        # Retry query with new identity if using Tor (max 10 attempts)
        if 'form id="captcha-form"' in response.text and self.tor:
            attempt += 1
            if attempt > 10:
                raise TorError("Tor query failed -- max attempts exceeded 10")
            return self.send((base_url or self.search_url), query, attempt)

        return response

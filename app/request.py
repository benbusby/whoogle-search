from app import rhyme
from app.filter import Filter
from io import BytesIO
import pycurl
import urllib.parse as urlparse

# Base search url
SEARCH_URL = 'https://www.google.com/search?gbv=1&q='

MOBILE_UA = '{}/5.0 (Android 0; Mobile; rv:54.0) Gecko/54.0 {}/59.0'
DESKTOP_UA = '{}/5.0 (X11; {} x86_64; rv:75.0) Gecko/20100101 {}/75.0'


def gen_user_agent(normal_ua):
    is_mobile = 'Android' in normal_ua or 'iPhone' in normal_ua

    mozilla = rhyme.get_rhyme('Mo') + rhyme.get_rhyme('zilla')
    firefox = rhyme.get_rhyme('Fire') + rhyme.get_rhyme('fox')
    linux = rhyme.get_rhyme('Lin') + 'ux'

    if is_mobile:
        return MOBILE_UA.format(mozilla, firefox)
    else:
        return DESKTOP_UA.format(mozilla, linux, firefox)


def gen_query(q, args, near_city=None):
    # Use :past(hour/day/week/month/year) if available
    # example search "new restaurants :past month"
    tbs = ''
    if ':past' in q:
        time_range = str.strip(q.split(':past', 1)[-1])
        tbs = '&tbs=qdr:' + str.lower(time_range[0])

    # Ensure search query is parsable
    q = urlparse.quote(q)

    # Pass along type of results (news, images, books, etc)
    tbm = ''
    if 'tbm' in args:
        tbm = '&tbm=' + args.get('tbm')

    # Get results page start value (10 per page, ie page 2 start val = 20)
    start = ''
    if 'start' in args:
        start = '&start=' + args.get('start')

    # Search for results near a particular city, if available
    near = ''
    if near_city is not None:
        near = '&near=' + urlparse.quote(near_city)

    return q + tbs + tbm + start + near


class Request:
    def __init__(self, normal_ua):
        self.modified_user_agent = gen_user_agent(normal_ua)

    def __getitem__(self, name):
        return getattr(self, name)

    def send(self, base_url=SEARCH_URL, query=''):
        response_header = []

        b_obj = BytesIO()
        crl = pycurl.Curl()
        crl.setopt(crl.URL, base_url + query)
        crl.setopt(crl.USERAGENT, self.modified_user_agent)
        crl.setopt(crl.WRITEDATA, b_obj)
        crl.setopt(crl.HEADERFUNCTION, response_header.append)
        crl.setopt(pycurl.FOLLOWLOCATION, 1)
        crl.perform()
        crl.close()

        return b_obj.getvalue().decode('utf-8', 'ignore')

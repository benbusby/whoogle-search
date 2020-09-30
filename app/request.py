from lxml import etree
import random
import requests
from requests import Response
import urllib.parse as urlparse

# Core Google search URLs
SEARCH_URL = 'https://www.google.com/search?gbv=1&q='
AUTOCOMPLETE_URL = 'https://suggestqueries.google.com/complete/search?client=toolbar&'

MOBILE_UA = '{}/5.0 (Android 0; Mobile; rv:54.0) Gecko/54.0 {}/59.0'
DESKTOP_UA = '{}/5.0 (X11; {} x86_64; rv:75.0) Gecko/20100101 {}/75.0'

# Valid query params
VALID_PARAMS = ['tbs', 'tbm', 'start', 'near', 'source', 'nfpr']


def gen_user_agent(is_mobile):
    mozilla = random.choice(['Moo', 'Woah', 'Bro', 'Slow']) + 'zilla'
    firefox = random.choice(['Choir', 'Squier', 'Higher', 'Wire']) + 'fox'
    linux = random.choice(['Win', 'Sin', 'Gin', 'Fin', 'Kin']) + 'ux'

    if is_mobile:
        return MOBILE_UA.format(mozilla, firefox)

    return DESKTOP_UA.format(mozilla, linux, firefox)


def gen_query(query, args, config, near_city=None):
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

        # Occasionally the 'tbs' param provided by google also contains a field for 'lr', but formatted
        # strangely. This is a (admittedly not very elegant) solution for this.
        # Ex/ &tbs=qdr:h,lr:lang_1pl --> the lr param needs to be extracted and have the "1" digit removed in this case
        sub_lang = [_ for _ in result_tbs.split(',') if 'lr:' in _]
        sub_lang = sub_lang[0][sub_lang[0].find('lr:') + 3:len(sub_lang[0])] if len(sub_lang) > 0 else ''

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

    # Set language for results (lr) if source isn't set, otherwise use the result
    # language param provided by google (but with the strange digit(s) removed)
    if 'source' in args:
        param_dict['source'] = '&source=' + args.get('source')
        param_dict['lr'] = ('&lr=' + ''.join([_ for _ in sub_lang if not _.isdigit()])) if sub_lang else ''
    else:
        param_dict['lr'] = ('&lr=' + config.lang_search) if config.lang_search else ''

    # Set autocorrected search ignore
    if 'nfpr' in args:
        param_dict['nfpr'] = '&nfpr=' + args.get('nfpr')

    param_dict['cr'] = ('&cr=' + config.ctry) if config.ctry else ''
    param_dict['hl'] = ('&hl=' + config.lang_interface.replace('lang_', '')) if config.lang_interface else ''
    param_dict['safe'] = '&safe=' + ('active' if config.safe else 'off')

    for val in param_dict.values():
        if not val:
            continue
        query += val

    return query


class Request:
    def __init__(self, normal_ua, language='lang_en'):
        self.language = language
        self.mobile = 'Android' in normal_ua or 'iPhone' in normal_ua
        self.modified_user_agent = gen_user_agent(self.mobile)

    def __getitem__(self, name):
        return getattr(self, name)

    def autocomplete(self, query):
        ac_query = dict(hl=self.language, q=query)
        response = self.send(base_url=AUTOCOMPLETE_URL, query=urlparse.urlencode(ac_query)).text

        if response:
            dom = etree.fromstring(response)
            return dom.xpath('//suggestion/@data')

        return []

    def send(self, base_url=SEARCH_URL, query='') -> Response:
        headers = {
            'User-Agent': self.modified_user_agent
        }

        return requests.get(base_url + query, headers=headers)

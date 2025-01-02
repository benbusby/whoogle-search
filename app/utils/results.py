from app.models.config import Config
from app.models.endpoint import Endpoint
from app.utils.misc import list_to_dict
from bs4 import BeautifulSoup, NavigableString
import copy
from flask import current_app
import html
import os
import urllib.parse as urlparse
from urllib.parse import parse_qs
import re
import warnings

SKIP_ARGS = ['ref_src', 'utm']
SKIP_PREFIX = ['//www.', '//mobile.', '//m.']
GOOG_STATIC = 'www.gstatic.com'
G_M_LOGO_URL = 'https://www.gstatic.com/m/images/icons/googleg.gif'
GOOG_IMG = '/images/branding/searchlogo/1x/googlelogo'
LOGO_URL = GOOG_IMG + '_desk'
BLANK_B64 = ('data:image/png;base64,'
             'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAQAAAAnOwc2AAAAD0lEQVR42mNkw'
             'AIYh7IgAAVVAAuInjI5AAAAAElFTkSuQmCC')

# Ad keywords
BLACKLIST = [
    'ad', 'ads', 'anuncio', 'annuncio', 'annonce', 'Anzeige', '广告', '廣告',
    'Reklama', 'Реклама', 'Anunț', '광고', 'annons', 'Annonse', 'Iklan',
    '広告', 'Augl.', 'Mainos', 'Advertentie', 'إعلان', 'Գովազդ', 'विज्ञापन',
    'Reklam', 'آگهی', 'Reklāma', 'Reklaam', 'Διαφήμιση', 'מודעה', 'Hirdetés',
    'Anúncio', 'Quảng cáo', 'โฆษณา', 'sponsored', 'patrocinado', 'gesponsert',
    'Sponzorováno', '스폰서', 'Gesponsord', 'Sponsorisé'
]

SITE_ALTS = {
    'twitter.com': os.getenv('WHOOGLE_ALT_TW', 'farside.link/nitter'),
    'youtube.com': os.getenv('WHOOGLE_ALT_YT', 'farside.link/invidious'),
    'reddit.com': os.getenv('WHOOGLE_ALT_RD', 'farside.link/libreddit'),
    **dict.fromkeys([
        'medium.com',
        'levelup.gitconnected.com'
    ], os.getenv('WHOOGLE_ALT_MD', 'farside.link/scribe')),
    'imgur.com': os.getenv('WHOOGLE_ALT_IMG', 'farside.link/rimgo'),
    'wikipedia.org': os.getenv('WHOOGLE_ALT_WIKI', 'farside.link/wikiless'),
    'imdb.com': os.getenv('WHOOGLE_ALT_IMDB', 'farside.link/libremdb'),
    'quora.com': os.getenv('WHOOGLE_ALT_QUORA', 'farside.link/quetre'),
    'stackoverflow.com': os.getenv('WHOOGLE_ALT_SO', 'farside.link/anonymousoverflow')
}

# Include custom site redirects from WHOOGLE_REDIRECTS
SITE_ALTS.update(list_to_dict(re.split(',|:', os.getenv('WHOOGLE_REDIRECTS', ''))))


def contains_cjko(s: str) -> bool:
    """This function check whether or not a string contains Chinese, Japanese,
    or Korean characters. It employs regex and uses the u escape sequence to
    match any character in a set of Unicode ranges.

    Args:
        s (str): string to be checked

    Returns:
        bool: True if the input s contains the characters and False otherwise
    """
    unicode_ranges = ('\u4e00-\u9fff' # Chinese characters
                      '\u3040-\u309f' # Japanese hiragana
                      '\u30a0-\u30ff' # Japanese katakana
                      '\u4e00-\u9faf' # Japanese kanji
                      '\uac00-\ud7af' # Korean hangul syllables
                      '\u1100-\u11ff' # Korean hangul jamo
                      )
    return bool(re.search(fr'[{unicode_ranges}]', s))


def bold_search_terms(response: str, query: str) -> BeautifulSoup:
    """Wraps all search terms in bold tags (<b>). If any terms are wrapped
    in quotes, only that exact phrase will be made bold.

    Args:
        response: The initial response body for the query
        query: The original search query

    Returns:
        BeautifulSoup: modified soup object with bold items
    """
    response = BeautifulSoup(response, 'html.parser')

    def replace_any_case(element: NavigableString, target_word: str) -> None:
        # Replace all instances of the word, but maintaining the same case in
        # the replacement
        if len(element) == len(target_word):
            return

        # Ensure target word is escaped for regex
        target_word = re.escape(target_word)

        # Check if the word contains Chinese, Japanese, or Korean characters
        if contains_cjko(target_word):
            reg_pattern = fr'((?![{{}}<>-]){target_word}(?![{{}}<>-]))'
        else:
            reg_pattern = fr'\b((?![{{}}<>-]){target_word}(?![{{}}<>-]))\b'

        if re.match(r'.*[@_!#$%^&*()<>?/\|}{~:].*', target_word) or (
                element.parent and element.parent.name == 'style'):
            return

        element.replace_with(BeautifulSoup(
            re.sub(reg_pattern,
                   r'<b>\1</b>',
                   element,
                   flags=re.I), 'html.parser')
        )

    # Split all words out of query, grouping the ones wrapped in quotes
    for word in re.split(r'\s+(?=[^"]*(?:"[^"]*"[^"]*)*$)', query):
        word = re.sub(r'[@_!#$%^&*()<>?/\|}{~:]+', '', word)
        target = response.find_all(
            text=re.compile(r'' + re.escape(word), re.I))
        for nav_str in target:
            replace_any_case(nav_str, word)

    return response


def has_ad_content(element: str) -> bool:
    """Inspects an HTML element for ad related content

    Args:
        element: The HTML element to inspect

    Returns:
        bool: True/False for the element containing an ad

    """
    element_str = ''.join(filter(str.isalpha, element))
    return (element_str.upper() in (value.upper() for value in BLACKLIST)
            or 'ⓘ' in element)


def get_first_link(soup: BeautifulSoup) -> str:
    """Retrieves the first result link from the query response

    Args:
        soup: The BeautifulSoup response body

    Returns:
        str: A str link to the first result

    """
    first_link = ''
    orig_details = []

    # Temporarily remove details so we don't grab those links
    for details in soup.find_all('details'):
        temp_details = soup.new_tag('removed_details')
        orig_details.append(details.replace_with(temp_details))

    # Replace hrefs with only the intended destination (no "utm" type tags)
    for a in soup.find_all('a', href=True):
        # Return the first search result URL
        if a['href'].startswith('http://') or a['href'].startswith('https://'):
            first_link = a['href']
            break

    # Add the details back
    for orig_detail, details in zip(orig_details, soup.find_all('removed_details')):
        details.replace_with(orig_detail)

    return first_link


def get_site_alt(link: str, site_alts: dict = SITE_ALTS) -> str:
    """Returns an alternative to a particular site, if one is configured

    Args:
        link: A string result URL to check against the site_alts map
        site_alts: A map of site alternatives to replace with. defaults to SITE_ALTS

    Returns:
        str: An updated (or ignored) result link

    """
    # Need to replace full hostname with alternative to encapsulate
    # subdomains as well
    parsed_link = urlparse.urlparse(link)

    # Extract subdomain separately from the domain+tld. The subdomain
    # is used for wikiless translations.
    split_host = parsed_link.netloc.split('.')
    subdomain = split_host[0] if len(split_host) > 2 else ''
    hostname = '.'.join(split_host[-2:])

    # The full scheme + hostname is used when comparing against the list of
    # available alternative services, due to how Medium links are constructed.
    # (i.e. for medium.com: "https://something.medium.com" should match,
    # "https://medium.com/..." should match, but "philomedium.com" should not)
    hostcomp = f'{parsed_link.scheme}://{hostname}'

    for site_key in site_alts.keys():
        site_alt = f'{parsed_link.scheme}://{site_key}'
        if not hostname or site_alt not in hostcomp or not site_alts[site_key]:
            continue

        # Wikipedia -> Wikiless replacements require the subdomain (if it's
        # a 2-char language code) to be passed as a URL param to Wikiless
        # in order to preserve the language setting.
        params = ''
        if 'wikipedia' in hostname and len(subdomain) == 2:
            hostname = f'{subdomain}.{hostname}'
            params = f'?lang={subdomain}'
        elif 'medium' in hostname and len(subdomain) > 0:
            hostname = f'{subdomain}.{hostname}'

        parsed_alt = urlparse.urlparse(site_alts[site_key])
        link = link.replace(hostname, site_alts[site_key]) + params
        # If a scheme is specified in the alternative, this results in a
        # replaced link that looks like "https://http://altservice.tld".
        # In this case, we can remove the original scheme from the result
        # and use the one specified for the alt.
        if parsed_alt.scheme:
            link = '//'.join(link.split('//')[1:])

        for prefix in SKIP_PREFIX:
            if parsed_alt.scheme:
                # If a scheme is specified, remove everything before the
                # first occurence of it
                link = f'{parsed_alt.scheme}{link.split(parsed_alt.scheme, 1)[-1]}'
            else:
                # Otherwise, replace the first occurrence of the prefix
                link = link.replace(prefix, '//', 1)
        break

    return link


def filter_link_args(link: str) -> str:
    """Filters out unnecessary URL args from a result link

    Args:
        link: The string result link to check for extraneous URL params

    Returns:
        str: An updated (or ignored) result link

    """
    parsed_link = urlparse.urlparse(link)
    link_args = parse_qs(parsed_link.query)
    safe_args = {}

    if len(link_args) == 0 and len(parsed_link) > 0:
        return link

    for arg in link_args.keys():
        if arg in SKIP_ARGS:
            continue

        safe_args[arg] = link_args[arg]

    # Remove original link query and replace with filtered args
    link = link.replace(parsed_link.query, '')
    if len(safe_args) > 0:
        link = link + urlparse.urlencode(safe_args, doseq=True)
    else:
        link = link.replace('?', '')

    return link


def append_nojs(result: BeautifulSoup) -> None:
    """Appends a no-Javascript alternative for a search result

    Args:
        result: The search result to append a no-JS link to

    Returns:
        None

    """
    nojs_link = BeautifulSoup(features='html.parser').new_tag('a')
    nojs_link['href'] = f'{Endpoint.window}?nojs=1&location=' + result['href']
    nojs_link.string = ' NoJS Link'
    result.append(nojs_link)


def append_anon_view(result: BeautifulSoup, config: Config) -> None:
    """Appends an 'anonymous view' for a search result, where all site
    contents are viewed through Whoogle as a proxy.

    Args:
        result: The search result to append an anon view link to
        nojs: Remove Javascript from Anonymous View

    Returns:
        None

    """
    av_link = BeautifulSoup(features='html.parser').new_tag('a')
    nojs = 'nojs=1' if config.nojs else 'nojs=0'
    location = f'location={result["href"]}'
    av_link['href'] = f'{Endpoint.window}?{nojs}&{location}'
    translation = current_app.config['TRANSLATIONS'][
       config.get_localization_lang()
    ]
    av_link.string = f'{translation["anon-view"]}'
    av_link['class'] = 'anon-view'
    result.append(av_link)

def check_currency(response: str) -> dict:
    """Check whether the results have currency conversion

    Args:
        response: Search query Result

    Returns:
        dict: Consists of currency names and values

    """
    soup = BeautifulSoup(response, 'html.parser')
    currency_link = soup.find('a', {'href': 'https://g.co/gfd'})
    if currency_link:
        while 'class' not in currency_link.attrs or \
                'ZINbbc' not in currency_link.attrs['class']:
            if currency_link.parent:
                currency_link = currency_link.parent
            else:
                return {}
        currency_link = currency_link.find_all(class_='BNeawe')
        currency1 = currency_link[0].text
        currency2 = currency_link[1].text
        currency1 = currency1.rstrip('=').split(' ', 1)
        currency2 = currency2.split(' ', 1)

        # Handle differences in currency formatting
        # i.e. "5.000" vs "5,000"
        if currency2[0][-3] == ',':
            currency1[0] = currency1[0].replace('.', '')
            currency1[0] = currency1[0].replace(',', '.')
            currency2[0] = currency2[0].replace('.', '')
            currency2[0] = currency2[0].replace(',', '.')
        else:
            currency1[0] = currency1[0].replace(',', '')
            currency2[0] = currency2[0].replace(',', '')

        currency1_value = float(re.sub(r'[^\d\.]', '', currency1[0]))
        currency1_label = currency1[1]

        currency2_value = float(re.sub(r'[^\d\.]', '', currency2[0]))
        currency2_label = currency2[1]

        return {'currencyValue1': currency1_value,
                'currencyLabel1': currency1_label,
                'currencyValue2': currency2_value,
                'currencyLabel2': currency2_label
                }
    return {}


def add_currency_card(soup: BeautifulSoup,
                      conversion_details: dict) -> BeautifulSoup:
    """Adds the currency conversion boxes
    to response of the search query

    Args:
        soup: Parsed search result
        conversion_details: Dictionary of currency
        related information

    Returns:
        BeautifulSoup
    """
    # Element before which the code will be changed
    # (This is the 'disclaimer' link)
    element1 = soup.find('a', {'href': 'https://g.co/gfd'})

    while 'class' not in element1.attrs or \
            'nXE3Ob' not in element1.attrs['class']:
        element1 = element1.parent

    # Creating the conversion factor
    conversion_factor = (conversion_details['currencyValue1'] /
                         conversion_details['currencyValue2'])

    # Creating a new div for the input boxes
    conversion_box = soup.new_tag('div')
    conversion_box['class'] = 'conversion_box'

    # Currency to be converted from
    input_box1 = soup.new_tag('input')
    input_box1['id'] = 'cb1'
    input_box1['type'] = 'number'
    input_box1['class'] = 'cb'
    input_box1['value'] = conversion_details['currencyValue1']
    input_box1['oninput'] = f'convert(1, 2, {1 / conversion_factor})'

    label_box1 = soup.new_tag('label')
    label_box1['for'] = 'cb1'
    label_box1['class'] = 'cb_label'
    label_box1.append(conversion_details['currencyLabel1'])

    br = soup.new_tag('br')

    # Currency to be converted to
    input_box2 = soup.new_tag('input')
    input_box2['id'] = 'cb2'
    input_box2['type'] = 'number'
    input_box2['class'] = 'cb'
    input_box2['value'] = conversion_details['currencyValue2']
    input_box2['oninput'] = f'convert(2, 1, {conversion_factor})'

    label_box2 = soup.new_tag('label')
    label_box2['for'] = 'cb2'
    label_box2['class'] = 'cb_label'
    label_box2.append(conversion_details['currencyLabel2'])

    conversion_box.append(input_box1)
    conversion_box.append(label_box1)
    conversion_box.append(br)
    conversion_box.append(input_box2)
    conversion_box.append(label_box2)

    element1.insert_before(conversion_box)
    return soup


def get_tabs_content(tabs: dict,
                     full_query: str,
                     search_type: str,
                     preferences: str,
                     translation: dict) -> dict:
    """Takes the default tabs content and updates it according to the query.

    Args:
        tabs: The default content for the tabs
        full_query: The original search query
        search_type: The current search_type
        translation: The translation to get the names of the tabs

    Returns:
        dict: contains the name, the href and if the tab is selected or not
    """
    map_query = full_query
    if '-site:' in full_query:
        block_idx = full_query.index('-site:')
        map_query = map_query[:block_idx]
    tabs = copy.deepcopy(tabs)
    for tab_id, tab_content in tabs.items():
        # update name to desired language
        if tab_id in translation:
            tab_content['name'] = translation[tab_id]

        # update href with query
        query = full_query.replace(f'&tbm={search_type}', '')

        if tab_content['tbm'] is not None:
            query = f"{query}&tbm={tab_content['tbm']}"

        if preferences:
            query = f"{query}&preferences={preferences}"

        tab_content['href'] = tab_content['href'].format(
            query=query,
            map_query=map_query)

        # update if selected tab (default all tab is selected)
        if tab_content['tbm'] == search_type:
            tabs['all']['selected'] = False
            tab_content['selected'] = True
    return tabs

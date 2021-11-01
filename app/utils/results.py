from bs4 import BeautifulSoup, NavigableString
import html
import os
import urllib.parse as urlparse
from urllib.parse import parse_qs
import re

SKIP_ARGS = ['ref_src', 'utm']
SKIP_PREFIX = ['//www.', '//mobile.', '//m.']
GOOG_STATIC = 'www.gstatic.com'
GOOG_IMG = '/images/branding/searchlogo/1x/googlelogo'
LOGO_URL = GOOG_IMG + '_desk'
BLANK_B64 = ('data:image/png;base64,'
             'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAQAAAAnOwc2AAAAD0lEQVR42mNkw'
             'AIYh7IgAAVVAAuInjI5AAAAAElFTkSuQmCC')

# Ad keywords
BLACKLIST = [
    'ad', 'anuncio', 'annuncio', 'annonce', 'Anzeige', '广告', '廣告', 'Reklama',
    'Реклама', 'Anunț', '광고', 'annons', 'Annonse', 'Iklan', '広告', 'Augl.',
    'Mainos', 'Advertentie', 'إعلان', 'Գովազդ', 'विज्ञापन', 'Reklam', 'آگهی',
    'Reklāma', 'Reklaam', 'Διαφήμιση', 'מודעה', 'Hirdetés', 'Anúncio'
]

SITE_ALTS = {
    'twitter.com': os.getenv('WHOOGLE_ALT_TW', 'nitter.net'),
    'youtube.com': os.getenv('WHOOGLE_ALT_YT', 'invidious.snopyta.org'),
    'instagram.com': os.getenv('WHOOGLE_ALT_IG', 'bibliogram.art/u'),
    'reddit.com': os.getenv('WHOOGLE_ALT_RD', 'libredd.it'),
    **dict.fromkeys([
        'medium.com',
        'levelup.gitconnected.com'
    ], os.getenv('WHOOGLE_ALT_MD', 'scribe.rip'))
}


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

        if not re.match('.*[a-zA-Z0-9].*', target_word) or (
                element.parent and element.parent.name == 'style'):
            return

        element.replace_with(BeautifulSoup(
            re.sub(fr'\b((?![{{}}<>-]){target_word}(?![{{}}<>-]))\b',
                   r'<b>\1</b>',
                   html.escape(element),
                   flags=re.I), 'html.parser')
        )

    # Split all words out of query, grouping the ones wrapped in quotes
    for word in re.split(r'\s+(?=[^"]*(?:"[^"]*"[^"]*)*$)', query):
        word = re.sub(r'[^A-Za-z0-9 ]+', '', word)
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
    return (element.upper() in (value.upper() for value in BLACKLIST)
            or 'ⓘ' in element)


def get_first_link(soup: BeautifulSoup) -> str:
    """Retrieves the first result link from the query response

    Args:
        soup: The BeautifulSoup response body

    Returns:
        str: A str link to the first result

    """
    # Replace hrefs with only the intended destination (no "utm" type tags)
    for a in soup.find_all('a', href=True):
        # Return the first search result URL
        if 'url?q=' in a['href']:
            return filter_link_args(a['href'])
    return ''


def get_site_alt(link: str) -> str:
    """Returns an alternative to a particular site, if one is configured

    Args:
        link: A string result URL to check against the SITE_ALTS map

    Returns:
        str: An updated (or ignored) result link

    """
    # Need to replace full hostname with alternative to encapsulate
    # subdomains as well
    hostname = urlparse.urlparse(link).hostname

    for site_key in SITE_ALTS.keys():
        if not hostname or site_key not in hostname:
            continue

        link = link.replace(hostname, SITE_ALTS[site_key])
        for prefix in SKIP_PREFIX:
            link = link.replace(prefix, '//')
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
    nojs_link['href'] = '/window?location=' + result['href']
    nojs_link.string = ' NoJS Link'
    result.append(nojs_link)


def add_ip_card(html_soup: BeautifulSoup, ip: str) -> BeautifulSoup:
    """Adds the client's IP address to the search results
        if query contains keywords

    Args:
        html_soup: The parsed search result containing the keywords
        ip: ip address of the client

    Returns:
        BeautifulSoup

    """
    if (not html_soup.select_one(".EY24We")
            and html_soup.select_one(".OXXup").get_text().lower() == "all"):
        # HTML IP card tag
        ip_tag = html_soup.new_tag("div")
        ip_tag["class"] = "ZINbbc xpd O9g5cc uUPGi"

        # For IP Address html tag
        ip_address = html_soup.new_tag("div")
        ip_address["class"] = "kCrYT ip-address-div"
        ip_address.string = ip

        # Text below the IP address
        ip_text = html_soup.new_tag("div")
        ip_text.string = "Your public IP address"
        ip_text["class"] = "kCrYT ip-text-div"

        # Adding all the above html tags to the IP card
        ip_tag.append(ip_address)
        ip_tag.append(ip_text)

        # Finding the element before which the IP card would be placed
        f_link = html_soup.select_one(".BNeawe.vvjwJb.AP7Wnd")
        ref_element = f_link.find_parent(class_="ZINbbc xpd O9g5cc" +
                                                " uUPGi")

        # Inserting the element
        ref_element.insert_before(ip_tag)
    return html_soup

from bs4 import BeautifulSoup
import os
import urllib.parse as urlparse
from urllib.parse import parse_qs


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
    'reddit.com': os.getenv('WHOOGLE_ALT_RD', 'libredd.it')
}


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

    for site_key in SITE_ALTS.keys():
        if site_key not in link:
            continue

        link = link.replace(site_key, SITE_ALTS[site_key])
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
    nojs_link['style'] = 'display:block;width:100%;'
    nojs_link.string = 'NoJS Link: ' + nojs_link['href']
    result.append(BeautifulSoup('<br><hr><br>', 'html.parser'))
    result.append(nojs_link)

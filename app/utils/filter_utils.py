from bs4 import BeautifulSoup
import os
import urllib.parse as urlparse
from urllib.parse import parse_qs

SKIP_ARGS = ['ref_src', 'utm']
FULL_RES_IMG = '<br/><a href="{}">Full Image</a>'
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
    'instagram.com': os.getenv('WHOOGLE_ALT_IG', 'bibliogram.art/u')
}


def has_ad_content(element: str):
    return element.upper() in (value.upper() for value in BLACKLIST) \
           or 'ⓘ' in element


def get_first_link(soup):
    # Replace hrefs with only the intended destination (no "utm" type tags)
    for a in soup.find_all('a', href=True):
        # Return the first search result URL
        if 'url?q=' in a['href']:
            return filter_link_args(a['href'])


def get_site_alt(link: str):
    for site_key in SITE_ALTS.keys():
        if site_key not in link:
            continue

        link = link.replace(site_key, SITE_ALTS[site_key])
        break

    return link.replace('www.', '').replace('//m.', '//')


def filter_link_args(query_link):
    parsed_link = urlparse.urlparse(query_link)
    link_args = parse_qs(parsed_link.query)
    safe_args = {}

    if len(link_args) == 0 and len(parsed_link) > 0:
        return query_link

    for arg in link_args.keys():
        if arg in SKIP_ARGS:
            continue

        safe_args[arg] = link_args[arg]

    # Remove original link query and replace with filtered args
    query_link = query_link.replace(parsed_link.query, '')
    if len(safe_args) > 0:
        query_link = query_link + urlparse.urlencode(safe_args, doseq=True)
    else:
        query_link = query_link.replace('?', '')

    return query_link


def gen_nojs(sibling):
    nojs_link = BeautifulSoup(features='html.parser').new_tag('a')
    nojs_link['href'] = '/window?location=' + sibling['href']
    nojs_link['style'] = 'display:block;width:100%;'
    nojs_link.string = 'NoJS Link: ' + nojs_link['href']
    sibling.append(BeautifulSoup('<br><hr><br>', 'html.parser'))
    sibling.append(nojs_link)

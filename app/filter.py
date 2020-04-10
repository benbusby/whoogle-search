from bs4 import BeautifulSoup
import re
import urllib.parse as urlparse
from urllib.parse import parse_qs

AD_CLASS = 'ZINbbc'
SPONS_CLASS = 'D1fz0e'


def reskin(page, dark_mode=False):
    # Aesthetic only re-skinning
    page = page.replace('>G<', '>Sh<')
    pattern = re.compile('4285f4|ea4335|fbcc05|34a853|fbbc05', re.IGNORECASE)
    page = pattern.sub('685e79', page)
    if dark_mode:
        page = page.replace('fff', '000').replace('202124', 'ddd').replace('1967D2', '3b85ea')

    return page


def gen_query(q, args, near_city=None):
    # Use :past(hour/day/week/month/year) if available
    # example search "new restaurants :past month"
    tbs = ''
    # if 'tbs' in request.args:
    #     tbs = '&tbs=' + request.args.get('tbs')
    #     q = q.replace(q.split(':past', 1)[-1], '').replace(':past', '')
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

    # Grab city from config, if available
    near = ''
    if near_city:
        near = '&near=' + urlparse.quote(near_city)

    return q + tbs + tbm + start + near


def cook(soup, user_agent, nojs=False, dark_mode=False):
    # Remove all ads (TODO: Ad specific div classes probably change over time, look into a more generic method)
    main_divs = soup.find('div', {'id': 'main'})
    if main_divs is not None:
        ad_divs = main_divs.findAll('div', {'class': AD_CLASS}, recursive=False)
        sponsored_divs = main_divs.findAll('div', {'class': SPONS_CLASS}, recursive=False)
        for div in ad_divs + sponsored_divs:
            div.decompose()

    # Remove unnecessary button(s)
    for button in soup.find_all('button'):
        button.decompose()

    # Remove svg logos
    for svg in soup.find_all('svg'):
        svg.decompose()

    # Update logo
    logo = soup.find('a', {'class': 'l'})
    if logo is not None and ('Android' in user_agent or 'iPhone' in user_agent):
        logo.insert(0, 'Shoogle')
        logo['style'] = 'display: flex;justify-content: center;align-items: center;color: #685e79;font-size: 18px;'

    # Replace hrefs with only the intended destination (no "utm" type tags)
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/advanced_search' in href:
            a.decompose()
            continue

        if 'url?q=' in href:
            # Strip unneeded arguments
            href = urlparse.urlparse(href)
            href = parse_qs(href.query)['q'][0]

            # Add no-js option
            if nojs:
                nojs_link = soup.new_tag('a')
                nojs_link['href'] = '/window?location=' + href
                nojs_link['style'] = 'display:block;width:100%;'
                nojs_link.string = 'NoJS Link: ' + nojs_link['href']
                a.append(BeautifulSoup('<br><hr><br>', 'html.parser'))
                a.append(nojs_link)

    # Set up dark mode if active
    if dark_mode:
        soup.find('html')['style'] = 'scrollbar-color: #333 #111;'
        for input_element in soup.findAll('input'):
            input_element['style'] = 'color:#fff;'

    # Ensure no extra scripts passed through
    try:
        for script in soup('script'):
            script.decompose()
        soup.find('div', id='sfooter').decompose()
    except Exception:
        pass

    return soup

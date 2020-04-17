from bs4 import BeautifulSoup
import re
import urllib.parse as urlparse
from urllib.parse import parse_qs


class Filter:
    def __init__(self, mobile=False, config=None):
        if config is None:
            config = {}

        self.near = config['near'] if 'near' in config else None
        self.dark = config['dark'] if 'dark' in config else False
        self.nojs = config['nojs'] if 'nojs' in config else False
        self.mobile = mobile

    def reskin(self, page):
        # Aesthetic only re-skinning
        page = page.replace('>G<', '>Sh<')
        pattern = re.compile('4285f4|ea4335|fbcc05|34a853|fbbc05', re.IGNORECASE)
        page = pattern.sub('685e79', page)
        if self.dark:
            page = page.replace('fff', '000').replace('202124', 'ddd').replace('1967D2', '3b85ea')

        return page

    def gen_query(self, q, args):
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

        # Grab city from config, if available
        near = ''
        if self.near:
            near = '&near=' + urlparse.quote(self.near)

        return q + tbs + tbm + start + near

    def clean(self, soup):
        # Remove all ads
        main_divs = soup.find('div', {'id': 'main'})
        if main_divs is not None:
            result_divs = main_divs.findAll('div', recursive=False)

            # Only ads/sponsored content use classes in the list of result divs
            ad_divs = [ad_div for ad_div in result_divs if 'class' in ad_div.attrs]
            for div in ad_divs:
                div.decompose()

        # Remove unnecessary button(s)
        for button in soup.find_all('button'):
            button.decompose()

        # Remove svg logos
        for svg in soup.find_all('svg'):
            svg.decompose()

        # Update logo
        logo = soup.find('a', {'class': 'l'})
        if logo and self.mobile:
            logo['style'] = 'display:flex; justify-content:center; align-items:center; color:#685e79; font-size:18px;'

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
                if self.nojs:
                    nojs_link = soup.new_tag('a')
                    nojs_link['href'] = '/window?location=' + href
                    nojs_link['style'] = 'display:block;width:100%;'
                    nojs_link.string = 'NoJS Link: ' + nojs_link['href']
                    a.append(BeautifulSoup('<br><hr><br>', 'html.parser'))
                    a.append(nojs_link)

        # Set up dark mode if active
        if self.dark:
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

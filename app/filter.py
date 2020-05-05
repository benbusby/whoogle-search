from app.request import VALID_PARAMS
from bs4 import BeautifulSoup
from cryptography.fernet import Fernet
import re
import urllib.parse as urlparse
from urllib.parse import parse_qs

SKIP_ARGS = ['ref_src', 'utm']
FULL_RES_IMG = '<br/><a href="{}">Full Image</a>'
GOOG_IMG = '/images/branding/searchlogo/1x/googlelogo'
LOGO_URL = GOOG_IMG + '_desk'
BLANK_B64 = '''
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAQAAAAnOwc2AAAAD0lEQVR42mNkwAIYh7IgAAVVAAuInjI5AAAAAElFTkSuQmCC
'''


class Filter:
    def __init__(self, mobile=False, config=None, secret_key=''):
        if config is None:
            config = {}

        self.near = config['near'] if 'near' in config else None
        self.dark = config['dark'] if 'dark' in config else False
        self.nojs = config['nojs'] if 'nojs' in config else False
        self.mobile = mobile
        self.secret_key = secret_key

    def __getitem__(self, name):
        return getattr(self, name)

    def reskin(self, page):
        # Aesthetic only re-skinning
        page = page.replace('>G<', '>Wh<')
        pattern = re.compile('4285f4|ea4335|fbcc05|34a853|fbbc05', re.IGNORECASE)
        page = pattern.sub('685e79', page)
        if self.dark:
            page = page.replace('fff', '000').replace('202124', 'ddd').replace('1967D2', '3b85ea')

        return page

    def clean(self, soup):
        self.remove_ads(soup)
        self.update_image_paths(soup)
        self.update_styling(soup)
        self.update_links(soup)

        input_form = soup.find('form')
        if input_form is not None:
            input_form['method'] = 'POST'

        # Ensure no extra scripts passed through
        for script in soup('script'):
            script.decompose()

        footer = soup.find('div', id='sfooter')
        if footer is not None:
            footer.decompose()

        return soup

    def remove_ads(self, soup):
        main_divs = soup.find('div', {'id': 'main'})
        if main_divs is None:
            return
        result_divs = main_divs.find_all('div', recursive=False)

        # Only ads/sponsored content use classes in the list of result divs
        ad_divs = [ad_div for ad_div in result_divs if 'class' in ad_div.attrs]
        for div in ad_divs:
            div.decompose()

    def update_image_paths(self, soup):
        for img in [_ for _ in soup.find_all('img') if 'src' in _.attrs]:
            img_src = img['src']
            if img_src.startswith('//'):
                img_src = 'https:' + img_src
            elif img_src.startswith(GOOG_IMG):
                # Special rebranding for image search results
                if img_src.startswith(LOGO_URL):
                    img['src'] = '/static/img/logo.png'
                    img['height'] = 40
                else:
                    img['src'] = BLANK_B64

                continue

            enc_src = Fernet(self.secret_key).encrypt(img_src.encode())
            img['src'] = '/tmp?image_url=' + enc_src.decode()
            # TODO: Non-mobile image results link to website instead of image
            # if not self.mobile:
            # img.append(BeautifulSoup(FULL_RES_IMG.format(img_src), 'html.parser'))

    def update_styling(self, soup):
        # Remove unnecessary button(s)
        for button in soup.find_all('button'):
            button.decompose()

        # Remove svg logos
        for svg in soup.find_all('svg'):
            svg.decompose()

        # Update logo
        logo = soup.find('a', {'class': 'l'})
        if logo and self.mobile:
            logo['style'] = 'display:flex; justify-content:center; align-items:center; color:#685e79; ' \
                            'font-size:18px; '

        # Fix search bar length on mobile
        try:
            search_bar = soup.find('header').find('form').find('div')
            search_bar['style'] = 'width: 100%;'
        except AttributeError:
            pass

        # Set up dark mode if active
        if self.dark:
            soup.find('html')['style'] = 'scrollbar-color: #333 #111;'
            for input_element in soup.findAll('input'):
                input_element['style'] = 'color:#fff;'

    def update_links(self, soup):
        # Replace hrefs with only the intended destination (no "utm" type tags)
        for a in soup.find_all('a', href=True):
            href = a['href'].replace('https://www.google.com', '')
            if '/advanced_search' in href:
                a.decompose()
                continue

            result_link = urlparse.urlparse(href)
            query_link = parse_qs(result_link.query)['q'][0] if '?q=' in href else ''

            if '/search?q=' in href:
                enc_result = Fernet(self.secret_key).encrypt(query_link.encode())
                new_search = '/search?q=' + enc_result.decode()

                query_params = parse_qs(urlparse.urlparse(href).query)
                for param in VALID_PARAMS:
                    param_val = query_params[param][0] if param in query_params else ''
                    new_search += '&' + param + '=' + param_val
                a['href'] = new_search
            elif 'url?q=' in href:
                # Strip unneeded arguments
                parsed_link = urlparse.urlparse(query_link)
                link_args = parse_qs(parsed_link.query)
                safe_args = {}

                if len(link_args) == 0 and len(parsed_link) > 0:
                    a['href'] = query_link
                    continue

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

                a['href'] = query_link

                # Add no-js option
                if self.nojs:
                    gen_nojs(soup, query_link, a)
            else:
                a['href'] = href


def gen_nojs(soup, link, sibling):
    nojs_link = soup.new_tag('a')
    nojs_link['href'] = '/window?location=' + link
    nojs_link['style'] = 'display:block;width:100%;'
    nojs_link.string = 'NoJS Link: ' + nojs_link['href']
    sibling.append(BeautifulSoup('<br><hr><br>', 'html.parser'))
    sibling.append(nojs_link)

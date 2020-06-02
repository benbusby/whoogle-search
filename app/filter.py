from app.request import VALID_PARAMS
from bs4 import BeautifulSoup
from bs4.element import ResultSet
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


def get_first_link(soup):
    # Replace hrefs with only the intended destination (no "utm" type tags)
    for a in soup.find_all('a', href=True):
        # Return the first search result URL
        if 'url?q=' in a['href']:
            return filter_link_args(a['href'])


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


def has_ad_content(element):
    return element == 'ad' or element == 'sponsoredⓘ'


class Filter:
    def __init__(self, user_keys: dict, mobile=False, config=None):
        if config is None:
            config = {}

        self.near = config['near'] if 'near' in config else ''
        self.dark = config['dark'] if 'dark' in config else False
        self.nojs = config['nojs'] if 'nojs' in config else False
        self.new_tab = config['new_tab'] if 'new_tab' in config else False
        self.mobile = mobile
        self.user_keys = user_keys
        self.main_divs = ResultSet('')
        self._elements = 0

    def __getitem__(self, name):
        return getattr(self, name)

    @property
    def elements(self):
        return self._elements

    def reskin(self, page):
        # Aesthetic only re-skinning
        page = page.replace('>G<', '>Wh<')
        pattern = re.compile('4285f4|ea4335|fbcc05|34a853|fbbc05', re.IGNORECASE)
        page = pattern.sub('685e79', page)
        if self.dark:
            page = page.replace('fff', '000').replace('202124', 'ddd').replace('1967D2', '3b85ea')

        return page

    def encrypt_path(self, msg, is_element=False):
        # Encrypts path to avoid plaintext results in logs
        if is_element:
            # Element paths are tracked differently in order for the element key to be regenerated
            # once all elements have been loaded
            enc_path = Fernet(self.user_keys['element_key']).encrypt(msg.encode()).decode()
            self._elements += 1
            return enc_path

        return Fernet(self.user_keys['text_key']).encrypt(msg.encode()).decode()

    def clean(self, soup):
        self.main_divs = soup.find('div', {'id': 'main'})
        self.remove_ads()
        self.fix_question_section()
        self.update_styling(soup)

        for img in [_ for _ in soup.find_all('img') if 'src' in _.attrs]:
            self.update_element_src(img, 'image/png')

        for audio in [_ for _ in soup.find_all('audio') if 'src' in _.attrs]:
            self.update_element_src(audio, 'audio/mpeg')

        for link in soup.find_all('a', href=True):
            self.update_link(link)

        input_form = soup.find('form')
        if input_form is not None:
            input_form['method'] = 'POST'

        # Ensure no extra scripts passed through
        for script in soup('script'):
            script.decompose()

        # Remove google's language/time config
        st_card = soup.find('div', id='st-card')
        if st_card:
            st_card.decompose()

        footer = soup.find('div', id='sfooter')
        if footer:
            footer.decompose()

        header = soup.find('header')
        if header:
            header.decompose()

        return soup

    def remove_ads(self):
        if not self.main_divs:
            return

        for div in [_ for _ in self.main_divs.find_all('div', recursive=True)]:
            has_ad = len([_ for _ in div.find_all('span', recursive=True) if has_ad_content(_.text.lower())])
            _ = div.decompose() if has_ad else None

    def fix_question_section(self):
        if not self.main_divs:
            return

        question_divs = [_ for _ in self.main_divs.find_all('div', recursive=False) if len(_.find_all('h2')) > 0]
        for x in question_divs:
            questions = [_ for _ in x.find_all('div', recursive=True) if _.text.endswith('?')]
            for question in questions:
                question['style'] = 'padding: 10px; font-style: italic;'

    def update_element_src(self, element, mimetype):
        element_src = element['src']
        if element_src.startswith('//'):
            element_src = 'https:' + element_src
        elif element_src.startswith(LOGO_URL):
            # Re-brand with Whoogle logo
            element['src'] = '/static/img/logo.png'
            element['style'] = 'height:40px;width:162px'
            return
        elif element_src.startswith(GOOG_IMG):
            element['src'] = BLANK_B64
            return

        element['src'] = '/element?url=' + self.encrypt_path(element_src, is_element=True) + \
                         '&type=' + urlparse.quote(mimetype)
        # TODO: Non-mobile image results link to website instead of image
        # if not self.mobile:
        # img.append(BeautifulSoup(FULL_RES_IMG.format(element_src), 'html.parser'))

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
            soup.find('html')['style'] = 'scrollbar-color: #333 #111;color:#fff !important;background:#000 !important'
            for input_element in soup.findAll('input'):
                input_element['style'] = 'color:#fff;background:#000;'

            for span_element in soup.findAll('span'):
                span_element['style'] = 'color: white;'

            for href_element in soup.findAll('a'):
                href_element['style'] = 'color: white' if href_element['href'].startswith('/search') else ''

    def update_link(self, link):
        # Replace href with only the intended destination (no "utm" type tags)
        href = link['href'].replace('https://www.google.com', '')
        if '/advanced_search' in href:
            link.decompose()
            return
        elif self.new_tab:
            link['target'] = '_blank'

        result_link = urlparse.urlparse(href)
        query_link = parse_qs(result_link.query)['q'][0] if '?q=' in href else ''

        if query_link.startswith('/'):
            link['href'] = 'https://google.com' + query_link
        elif '/search?q=' in href:
            new_search = '/search?q=' + self.encrypt_path(query_link)

            query_params = parse_qs(urlparse.urlparse(href).query)
            for param in VALID_PARAMS:
                param_val = query_params[param][0] if param in query_params else ''
                new_search += '&' + param + '=' + param_val
            link['href'] = new_search
        elif 'url?q=' in href:
            # Strip unneeded arguments
            link['href'] = filter_link_args(query_link)

            # Add no-js option
            if self.nojs:
                gen_nojs(link)
        else:
            link['href'] = href


def gen_nojs(sibling):
    nojs_link = BeautifulSoup().new_tag('a')
    nojs_link['href'] = '/window?location=' + sibling['href']
    nojs_link['style'] = 'display:block;width:100%;'
    nojs_link.string = 'NoJS Link: ' + nojs_link['href']
    sibling.append(BeautifulSoup('<br><hr><br>', 'html.parser'))
    sibling.append(nojs_link)

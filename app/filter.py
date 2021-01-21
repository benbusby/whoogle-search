from app.request import VALID_PARAMS
from app.utils.filter_utils import *
from bs4.element import ResultSet
from cryptography.fernet import Fernet
import re
import urllib.parse as urlparse
from urllib.parse import parse_qs


class Filter:
    def __init__(self, user_keys: dict, mobile=False, config=None):
        if config is None:
            config = {}

        self.near = config['near'] if 'near' in config else ''
        self.dark = config['dark'] if 'dark' in config else False
        self.nojs = config['nojs'] if 'nojs' in config else False
        self.new_tab = config['new_tab'] if 'new_tab' in config else False
        self.alt_redirect = config['alts'] if 'alts' in config else False
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
        if self.dark:
            page = page.replace(
                'fff', '000').replace(
                '202124', 'ddd').replace(
                '1967D2', '3b85ea')

        return page

    def encrypt_path(self, msg, is_element=False):
        # Encrypts path to avoid plaintext results in logs
        if is_element:
            # Element paths are encrypted separately from text, to allow key
            # regeneration once all items have been served to the user
            enc_path = Fernet(
                self.user_keys['element_key']
            ).encrypt(msg.encode()).decode()
            self._elements += 1
            return enc_path

        return Fernet(
            self.user_keys['text_key']
        ).encrypt(msg.encode()).decode()

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

        # Update default footer and header
        footer = soup.find('footer')
        if footer:
            # Remove divs that have multiple links beyond just page navigation
            [_.decompose() for _ in footer.find_all('div', recursive=False)
             if len(_.find_all('a', href=True)) > 3]

        header = soup.find('header')
        if header:
            header.decompose()

        return soup

    def remove_ads(self):
        if not self.main_divs:
            return

        for div in [_ for _ in self.main_divs.find_all('div', recursive=True)]:
            div_ads = [_ for _ in div.find_all('span', recursive=True)
                       if has_ad_content(_.text)]
            _ = div.decompose() if len(div_ads) else None

    def fix_question_section(self):
        if not self.main_divs:
            return

        question_divs = [_ for _ in self.main_divs.find_all(
            'div', recursive=False
        ) if len(_.find_all('h2')) > 0]

        if len(question_divs) == 0:
            return

        # Wrap section in details element to allow collapse/expand
        details = BeautifulSoup(features='html.parser').new_tag('details')
        summary = BeautifulSoup(features='html.parser').new_tag('summary')
        summary.string = question_divs[0].find('h2').text
        question_divs[0].find('h2').decompose()
        details.append(summary)
        question_divs[0].wrap(details)

        for question_div in question_divs:
            questions = [_ for _ in question_div.find_all(
                'div', recursive=True
            ) if _.text.endswith('?')]

            for question in questions:
                question['style'] = 'padding: 10px; font-style: italic;'

    def update_element_src(self, element, mime):
        element_src = element['src']
        if element_src.startswith('//'):
            element_src = 'https:' + element_src
        elif element_src.startswith(LOGO_URL):
            # Re-brand with Whoogle logo
            element['src'] = 'static/img/logo.png'
            element['style'] = 'height:40px;width:162px'
            return
        elif element_src.startswith(GOOG_IMG):
            element['src'] = BLANK_B64
            return

        element['src'] = 'element?url=' + self.encrypt_path(
            element_src,
            is_element=True) + '&type=' + urlparse.quote(mime)

        # FIXME: Non-mobile image results link to website instead of image
        # if not self.mobile:
        # img.append(
        #     BeautifulSoup(FULL_RES_IMG.format(element_src),
        #     'html.parser'))

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
            logo['style'] = ('display:flex; justify-content:center; '
                             'align-items:center; color:#685e79; '
                             'font-size:18px; ')

        # Fix search bar length on mobile
        try:
            search_bar = soup.find('header').find('form').find('div')
            search_bar['style'] = 'width: 100%;'
        except AttributeError:
            pass

    def update_link(self, link):
        # Replace href with only the intended destination (no "utm" type tags)
        href = link['href'].replace('https://www.google.com', '')
        if 'advanced_search' in href or 'tbm=shop' in href:
            # FIXME: The "Shopping" tab requires further filtering (see #136)
            # Temporarily removing all links to that tab for now.
            link.decompose()
            return
        elif self.new_tab:
            link['target'] = '_blank'

        result_link = urlparse.urlparse(href)
        query_link = parse_qs(
            result_link.query
        )['q'][0] if '?q=' in href else ''

        if query_link.startswith('/'):
            # Internal google links (i.e. mail, maps, etc) should still
            # be forwarded to Google
            link['href'] = 'https://google.com' + query_link
        elif '/search?q=' in href:
            # "li:1" implies the query should be interpreted verbatim,
            # which is accomplished by wrapping the query in double quotes
            if 'li:1' in href:
                query_link = '"' + query_link + '"'
            new_search = 'search?q=' + self.encrypt_path(query_link)

            query_params = parse_qs(urlparse.urlparse(href).query)
            for param in VALID_PARAMS:
                if param not in query_params:
                    continue
                param_val = query_params[param][0]
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

        # Replace link location if "alts" config is enabled
        if self.alt_redirect:
            # Search and replace all link descriptions
            # with alternative location
            link['href'] = get_site_alt(link['href'])
            link_desc = link.find_all(
                text=re.compile('|'.join(SITE_ALTS.keys())))
            if len(link_desc) == 0:
                return

            # Replace link destination
            link_desc[0].replace_with(get_site_alt(link_desc[0]))

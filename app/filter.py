from app.request import VALID_PARAMS, MAPS_URL
from app.utils.results import *
from bs4 import BeautifulSoup
from bs4.element import ResultSet, Tag
from cryptography.fernet import Fernet
from flask import render_template
import re
import urllib.parse as urlparse
from urllib.parse import parse_qs


def extract_q(q_str: str, href: str) -> str:
    """Extracts the 'q' element from a result link. This is typically
    either the link to a result's website, or a string.

    Args:
        q_str: The result link to parse
        href: The full url to check for standalone 'q' elements first,
              rather than parsing the whole query string and then checking.

    Returns:
        str: The 'q' element of the link, or an empty string
    """
    return parse_qs(q_str)['q'][0] if ('&q=' in href or '?q=' in href) else ''


def clean_query(query: str) -> str:
    """Strips the blocked site list from the query, if one is being
    used.

    Args:
        query: The query string

    Returns:
        str: The query string without any "-site:..." filters
    """
    return query[:query.find('-site:')] if '-site:' in query else query


class Filter:
    # Limit used for determining if a result is a "regular" result or a list
    # type result (such as "people also asked", "related searches", etc)
    RESULT_CHILD_LIMIT = 7

    def __init__(self, user_key: str, mobile=False, config=None) -> None:
        if config is None:
            config = {}

        self.near = config['near'] if 'near' in config else ''
        self.dark = config['dark'] if 'dark' in config else False
        self.nojs = config['nojs'] if 'nojs' in config else False
        self.new_tab = config['new_tab'] if 'new_tab' in config else False
        self.alt_redirect = config['alts'] if 'alts' in config else False
        self.mobile = mobile
        self.user_key = user_key
        self.main_divs = ResultSet('')
        self._elements = 0

    def __getitem__(self, name):
        return getattr(self, name)

    @property
    def elements(self):
        return self._elements

    def reskin(self, page: str) -> str:
        # Aesthetic only re-skinning
        if self.dark:
            page = page.replace(
                'fff', '000').replace(
                '202124', 'ddd').replace(
                '1967D2', '3b85ea')

        return page

    def encrypt_path(self, path, is_element=False) -> str:
        # Encrypts path to avoid plaintext results in logs
        if is_element:
            # Element paths are encrypted separately from text, to allow key
            # regeneration once all items have been served to the user
            enc_path = Fernet(self.user_key).encrypt(path.encode()).decode()
            self._elements += 1
            return enc_path

        return Fernet(self.user_key).encrypt(path.encode()).decode()

    def clean(self, soup) -> BeautifulSoup:
        self.main_divs = soup.find('div', {'id': 'main'})
        self.remove_ads()
        self.collapse_sections()
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

    def remove_ads(self) -> None:
        """Removes ads found in the list of search result divs

        Returns:
            None (The soup object is modified directly)
        """
        if not self.main_divs:
            return

        for div in [_ for _ in self.main_divs.find_all('div', recursive=True)]:
            div_ads = [_ for _ in div.find_all('span', recursive=True)
                       if has_ad_content(_.text)]
            _ = div.decompose() if len(div_ads) else None

    def collapse_sections(self) -> None:
        """Collapses long result sections ("people also asked", "related
         searches", etc) into "details" elements

        These sections are typically the only sections in the results page that
        have more than ~5 child divs within a primary result div.

        Returns:
            None (The soup object is modified directly)
        """
        def pull_child_divs(result_div: BeautifulSoup):
            try:
                return result_div.findChildren(
                    'div', recursive=False
                )[0].findChildren(
                    'div', recursive=False)
            except IndexError:
                return []

        if not self.main_divs:
            return

        # Loop through results and check for the number of child divs in each
        for result in self.main_divs:
            result_children = pull_child_divs(result)
            if len(result_children) < self.RESULT_CHILD_LIMIT:
                continue

            # Find and decompose the first element with an inner HTML text val.
            # This typically extracts the title of the section (i.e. "Related
            # Searches", "People also ask", etc)
            label = 'Collapsed Results'
            for elem in result_children:
                if elem.text:
                    label = elem.text
                    elem.decompose()
                    break

            # Create the new details element to wrap around the result's
            # first parent
            parent = None
            idx = 0
            while not parent and idx < len(result_children):
                parent = result_children[idx].parent
                idx += 1
            details = BeautifulSoup(features='html.parser').new_tag('details')
            summary = BeautifulSoup(features='html.parser').new_tag('summary')
            summary.string = label
            details.append(summary)

            if parent:
                parent.wrap(details)

    def update_element_src(self, element: Tag, mime: str) -> None:
        """Encrypts the original src of an element and rewrites the element src
        to use the "/element?src=" pass-through.

        Returns:
            None (The soup element is modified directly)

        """
        src = element['src']

        if src.startswith('//'):
            src = 'https:' + src

        if src.startswith(LOGO_URL):
            # Re-brand with Whoogle logo
            element.replace_with(BeautifulSoup(
                render_template('logo.html', dark=self.dark),
                features='html.parser'))
            return
        elif src.startswith(GOOG_IMG) or GOOG_STATIC in src:
            element['src'] = BLANK_B64
            return

        element['src'] = 'element?url=' + self.encrypt_path(
            src,
            is_element=True) + '&type=' + urlparse.quote(mime)

    def update_styling(self, soup) -> None:
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

    def update_link(self, link: Tag) -> None:
        """Update internal link paths with encrypted path, otherwise remove
        unnecessary redirects and/or marketing params from the url

        Args:
            link: A bs4 Tag element to inspect and update

        Returns:
            None (the tag is updated directly)

        """
        # Replace href with only the intended destination (no "utm" type tags)
        href = link['href'].replace('https://www.google.com', '')
        if 'advanced_search' in href or 'tbm=shop' in href:
            # FIXME: The "Shopping" tab requires further filtering (see #136)
            # Temporarily removing all links to that tab for now.
            link.decompose()
            return

        result_link = urlparse.urlparse(href)
        q = extract_q(result_link.query, href)

        if q.startswith('/'):
            # Internal google links (i.e. mail, maps, etc) should still
            # be forwarded to Google
            link['href'] = 'https://google.com' + q
        elif '/search?q=' in href:
            # "li:1" implies the query should be interpreted verbatim,
            # which is accomplished by wrapping the query in double quotes
            if 'li:1' in href:
                q = '"' + q + '"'
            new_search = 'search?q=' + self.encrypt_path(q)

            query_params = parse_qs(urlparse.urlparse(href).query)
            for param in VALID_PARAMS:
                if param not in query_params:
                    continue
                param_val = query_params[param][0]
                new_search += '&' + param + '=' + param_val
            link['href'] = new_search
        elif 'url?q=' in href:
            # Strip unneeded arguments
            link['href'] = filter_link_args(q)

            # Add no-js option
            if self.nojs:
                append_nojs(link)

            if self.new_tab:
                link['target'] = '_blank'
        else:
            if href.startswith(MAPS_URL):
                # Maps links don't work if a site filter is applied
                link['href'] = MAPS_URL + "?q=" + clean_query(q)
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

    def view_image(self, soup) -> BeautifulSoup:
        """Replaces the soup with a new one that handles mobile results and
        adds the link of the image full res to the results.

        Args:
            soup: A BeautifulSoup object containing the image mobile results.

        Returns:
            BeautifulSoup: The new BeautifulSoup object
        """

        # get some tags that are unchanged between mobile and pc versions
        search_input = soup.find_all('td', attrs={'class': "O4cRJf"})[0]
        search_options = soup.find_all('div', attrs={'class': "M7pB2"})[0]
        cor_suggested = soup.find_all('table', attrs={'class': "By0U9"})
        next_pages = soup.find_all('table', attrs={'class': "uZgmoc"})[0]
        information = soup.find_all('div', attrs={'class': "TuS8Ad"})[0]

        results = []
        # find results div
        results_div = soup.find_all('div', attrs={'class': "nQvrDb"})[0]
        # find all the results
        results_all = results_div.find_all('div', attrs={'class': "lIMUZd"})

        for item in results_all:
            urls = item.find('a')['href'].split('&imgrefurl=')

            img_url = urlparse.unquote(urls[0].replace('/imgres?imgurl=', ''))

            try:
                # Try to strip out only the necessary part of the web page link
                web_page = urlparse.unquote(urls[1].split('&')[0])
            except IndexError:
                web_page = urlparse.unquote(urls[1])

            img_tbn = urlparse.unquote(item.find('a').find('img')['src'])

            results.append({
                'domain': urlparse.urlparse(web_page).netloc,
                'img_url': img_url,
                'web_page': web_page,
                'img_tbn': img_tbn
            })

        soup = BeautifulSoup(render_template('imageresults.html',
                                             length=len(results),
                                             results=results,
                                             view_label="View Image"),
                             features='html.parser')
        # replace search input object
        soup.find_all('td',
                      attrs={'class': "O4cRJf"})[0].replaceWith(search_input)
        # replace search options object (All, Images, Videos, etc.)
        soup.find_all('div',
                      attrs={'class': "M7pB2"})[0].replaceWith(search_options)
        # replace correction suggested by google object if exists
        if len(cor_suggested):
            soup.find_all(
                'table',
                attrs={'class': "By0U9"}
            )[0].replaceWith(cor_suggested[0])
        # replace next page object at the bottom of the page
        soup.find_all('table',
                      attrs={'class': "uZgmoc"})[0].replaceWith(next_pages)
        # replace information about user connection at the bottom of the page
        soup.find_all('div',
                      attrs={'class': "TuS8Ad"})[0].replaceWith(information)
        return soup

from bs4 import BeautifulSoup


class GClasses:
    """A class for tracking obfuscated class names used in Google results that
    are directly referenced in Whoogle's filtering code.

    Note: Using these should be a last resort. It is always preferred to filter
    results using structural cues instead of referencing class names, as these
    are liable to change at any moment.
    """
    main_tbm_tab = 'KP7LCb'
    images_tbm_tab = 'n692Zd'
    footer = 'TuS8Ad'
    result_class_a = 'ZINbbc'
    result_class_b = 'luh4td'
    scroller_class = 'idg8be'

    result_classes = {
        result_class_a: ['Gx5Zad'],
        result_class_b: ['fP1Qef']
    }

    @classmethod
    def replace_css_classes(cls, soup: BeautifulSoup) -> BeautifulSoup:
        """Replace updated Google classes with the original class names that
        Whoogle relies on for styling.

        Args:
            soup: The result page as a BeautifulSoup object

        Returns:
            BeautifulSoup: The new BeautifulSoup
        """
        result_divs = soup.find_all('div', {
            'class': [_ for c in cls.result_classes.values() for _ in c]
        })

        for div in result_divs:
            new_class = ' '.join(div['class'])
            for key, val in cls.result_classes.items():
                new_class = ' '.join(new_class.replace(_, key) for _ in val)
            div['class'] = new_class.split(' ')
        return soup

    def __str__(self):
        return self.value

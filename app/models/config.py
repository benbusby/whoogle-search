from flask import current_app
import os


class Config:
    def __init__(self, **kwargs):
        app_config = current_app.config
        self.url = os.getenv('WHOOGLE_CONFIG_URL', '')
        self.lang_search = os.getenv('WHOOGLE_CONFIG_LANGUAGE', '')
        self.lang_interface = os.getenv('WHOOGLE_CONFIG_LANGUAGE', '')
        self.style = open(os.path.join(app_config['STATIC_FOLDER'],
                                       'css/variables.css')).read()
        self.ctry = os.getenv('WHOOGLE_CONFIG_COUNTRY', '')
        self.safe = bool(os.getenv('WHOOGLE_CONFIG_SAFE', False))
        self.dark = bool(os.getenv('WHOOGLE_CONFIG_DARK', False))
        self.alts = bool(os.getenv('WHOOGLE_CONFIG_ALTS', False))
        self.nojs = bool(os.getenv('WHOOGLE_CONFIG_NOJS', False))
        self.tor = bool(os.getenv('WHOOGLE_CONFIG_TOR', False))
        self.near = os.getenv('WHOOGLE_CONFIG_NEAR', '')
        self.new_tab = bool(os.getenv('WHOOGLE_CONFIG_NEW_TAB', False))
        self.get_only = bool(os.getenv('WHOOGLE_CONFIG_GET_ONLY', False))
        self.safe_keys = [
            'lang_search',
            'lang_interface',
            'ctry',
            'dark'
        ]

        for key, value in kwargs.items():
            if not value:
                continue
            setattr(self, key, value)

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        return setattr(self, name, value)

    def __delitem__(self, name):
        return delattr(self, name)

    def __contains__(self, name):
        return hasattr(self, name)

    def is_safe_key(self, key) -> bool:
        """Establishes a group of config options that are safe to set
        in the url.

        Args:
            key (str) -- the key to check against

        Returns:
            bool -- True/False depending on if the key is in the "safe"
            array
        """

        return key in self.safe_keys

    def from_params(self, params) -> 'Config':
        """Modify user config with search parameters. This is primarily
        used for specifying configuration on a search-by-search basis on
        public instances.

        Args:
            params -- the url arguments (can be any deemed safe by is_safe())

        Returns:
            Config -- a modified config object
        """
        for param_key in params.keys():
            if not self.is_safe_key(param_key):
                continue
            self[param_key] = params.get(param_key)
        return self

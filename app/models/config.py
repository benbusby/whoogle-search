class Config:
    def __init__(self, **kwargs):
        self.url = ''
        self.lang_search = ''
        self.lang_interface = ''
        self.ctry = ''
        self.safe = False
        self.dark = False
        self.nojs = False
        self.tor = False
        self.near = ''
        self.alts = False
        self.new_tab = False
        self.get_only = False
        self.safe_keys = [
            'lang_search',
            'lang_interface',
            'ctry',
            'dark'
        ]

        for key, value in kwargs.items():
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

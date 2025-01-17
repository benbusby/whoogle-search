from inspect import Attribute
from typing import Optional
from app.utils.misc import read_config_bool
from flask import current_app
import os
from base64 import urlsafe_b64encode, urlsafe_b64decode
from cryptography.fernet import Fernet
import hashlib
import brotli
import logging
import json

import cssutils
from cssutils.css.cssstylesheet import CSSStyleSheet
from cssutils.css.cssstylerule import CSSStyleRule

# removes warnings from cssutils
cssutils.log.setLevel(logging.CRITICAL)


def get_rule_for_selector(stylesheet: CSSStyleSheet,
                          selector: str) -> Optional[CSSStyleRule]:
    """Search for a rule that matches a given selector in a stylesheet.

    Args:
        stylesheet (CSSStyleSheet) -- the stylesheet to search
        selector (str) -- the selector to search for

    Returns:
        Optional[CSSStyleRule] -- the rule that matches the selector or None
    """
    for rule in stylesheet.cssRules:
        if hasattr(rule, "selectorText") and selector == rule.selectorText:
            return rule
    return None


class Config:
    def __init__(self, **kwargs):
        # User agent configuration
        self.user_agent = kwargs.get('user_agent', 'LYNX_UA')
        self.custom_user_agent = kwargs.get('custom_user_agent', '')
        self.use_custom_user_agent = kwargs.get('use_custom_user_agent', False)

        # Add user agent related keys to safe_keys
        self.safe_keys = [
            'lang_search',
            'lang_interface',
            'country',
            'theme',
            'alts',
            'new_tab',
            'view_image',
            'block',
            'safe',
            'nojs',
            'anon_view',
            'preferences_encrypted',
            'tbs',
            'user_agent',
            'custom_user_agent',
            'use_custom_user_agent'
        ]

        app_config = current_app.config
        self.url = kwargs.get('url', '')
        self.lang_search = kwargs.get('lang_search', '')
        self.lang_interface = kwargs.get('lang_interface', '')
        self.style_modified = os.getenv(
            'WHOOGLE_CONFIG_STYLE', '')
        self.block = os.getenv('WHOOGLE_CONFIG_BLOCK', '')
        self.block_title = os.getenv('WHOOGLE_CONFIG_BLOCK_TITLE', '')
        self.block_url = os.getenv('WHOOGLE_CONFIG_BLOCK_URL', '')
        self.country = os.getenv('WHOOGLE_CONFIG_COUNTRY', '')
        self.tbs = os.getenv('WHOOGLE_CONFIG_TIME_PERIOD', '')
        self.theme = kwargs.get('theme', '')
        self.safe = kwargs.get('safe', '')
        self.dark = kwargs.get('dark', '')
        self.alts = kwargs.get('alts', '')
        self.nojs = kwargs.get('nojs', '')
        self.tor = kwargs.get('tor', '')
        self.near = kwargs.get('near', '')
        self.new_tab = kwargs.get('new_tab', '')
        self.view_image = kwargs.get('view_image', '')
        self.get_only = kwargs.get('get_only', '')
        self.anon_view = read_config_bool('WHOOGLE_CONFIG_ANON_VIEW')
        self.preferences_encrypted = read_config_bool('WHOOGLE_CONFIG_PREFERENCES_ENCRYPTED')
        self.preferences_key = os.getenv('WHOOGLE_CONFIG_PREFERENCES_KEY', '')

        self.accept_language = False

        # Skip setting custom config if there isn't one
        if kwargs:
            mutable_attrs = self.get_mutable_attrs()
            for attr in mutable_attrs:
                if attr in kwargs.keys():
                    setattr(self, attr, kwargs[attr])
                elif attr not in kwargs.keys() and mutable_attrs[attr] == bool:
                    setattr(self, attr, False)

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        return setattr(self, name, value)

    def __delitem__(self, name):
        return delattr(self, name)

    def __contains__(self, name):
        return hasattr(self, name)

    def get_mutable_attrs(self):
        return {name: type(attr) for name, attr in self.__dict__.items()
                if not name.startswith("__")
                and (type(attr) is bool or type(attr) is str)}

    def get_attrs(self):
        return {name: attr for name, attr in self.__dict__.items()
                if not name.startswith("__")
                and (type(attr) is bool or type(attr) is str)}

    @property
    def style(self) -> str:
        """Returns the default style updated with specified modifications.

        Returns:
            str -- the new style
        """
        style_sheet = cssutils.parseString(
            open(os.path.join(current_app.config['STATIC_FOLDER'],
                              'css/variables.css')).read()
        )

        modified_sheet = cssutils.parseString(self.style_modified)
        for rule in modified_sheet:
            rule_default = get_rule_for_selector(style_sheet,
                                                 rule.selectorText)
            # if modified rule is in default stylesheet, update it
            if rule_default is not None:
                # TODO: update this in a smarter way to handle :root better
                # for now if we change a varialbe in :root all other default
                # variables need to be also present
                rule_default.style = rule.style
            # else add the new rule to the default stylesheet
            else:
                style_sheet.add(rule)
        return str(style_sheet.cssText, 'utf-8')

    @property
    def preferences(self) -> str:
        # if encryption key is not set will uncheck preferences encryption
        if self.preferences_encrypted:
            self.preferences_encrypted = bool(self.preferences_key)

        # add a tag for visibility if preferences token startswith 'e' it means
        # the token is encrypted, 'u' means the token is unencrypted and can be
        # used by other whoogle instances
        encrypted_flag = "e" if self.preferences_encrypted else 'u'
        preferences_digest = self._encode_preferences()
        return f"{encrypted_flag}{preferences_digest}"

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

    def get_localization_lang(self):
        """Returns the correct language to use for localization, but falls
        back to english if not set.

        Returns:
            str -- the localization language string
        """
        if (self.lang_interface and
                self.lang_interface in current_app.config['TRANSLATIONS']):
            return self.lang_interface

        return 'lang_en'

    def from_params(self, params) -> 'Config':
        """Modify user config with search parameters. This is primarily
        used for specifying configuration on a search-by-search basis on
        public instances.

        Args:
            params -- the url arguments (can be any deemed safe by is_safe())

        Returns:
            Config -- a modified config object
        """
        if 'preferences' in params:
            params_new = self._decode_preferences(params['preferences'])
            # if preferences leads to an empty dictionary it means preferences
            # parameter was not decrypted successfully
            if len(params_new):
                params = params_new 

        for param_key in params.keys():
            if not self.is_safe_key(param_key):
                continue
            param_val = params.get(param_key)

            if param_val == 'off':
                param_val = False
            elif isinstance(param_val, str):
                if param_val.isdigit():
                    param_val = int(param_val)

            self[param_key] = param_val
        return self

    def to_params(self, keys: list = []) -> str:
        """Generates a set of safe params for using in Whoogle URLs

        Args:
            keys (list) -- optional list of keys of URL parameters

        Returns:
            str -- a set of URL parameters
        """
        if not len(keys):
            keys = self.safe_keys

        param_str = ''
        for safe_key in keys:
            if not self[safe_key]:
                continue
            param_str = param_str + f'&{safe_key}={self[safe_key]}'

        return param_str

    def _get_fernet_key(self, password: str) -> bytes:
        hash_object = hashlib.md5(password.encode())
        key = urlsafe_b64encode(hash_object.hexdigest().encode())
        return key

    def _encode_preferences(self) -> str:
        preferences_json = json.dumps(self.get_attrs()).encode()
        compressed_preferences = brotli.compress(preferences_json)

        if self.preferences_encrypted and self.preferences_key:
            key = self._get_fernet_key(self.preferences_key)
            encrypted_preferences = Fernet(key).encrypt(compressed_preferences)
            compressed_preferences = brotli.compress(encrypted_preferences)

        return urlsafe_b64encode(compressed_preferences).decode()

    def _decode_preferences(self, preferences: str) -> dict:
        mode = preferences[0]
        preferences = preferences[1:]

        try:
            decoded_data = brotli.decompress(urlsafe_b64decode(preferences.encode() + b'=='))

            if mode == 'e' and self.preferences_key:
                # preferences are encrypted
                key = self._get_fernet_key(self.preferences_key)
                decrypted_data = Fernet(key).decrypt(decoded_data)
                decoded_data = brotli.decompress(decrypted_data)

            config = json.loads(decoded_data)
        except Exception:
            config = {}

        return config


from app.models.config import Config
from app.models.endpoint import Endpoint
from app.utils.misc import list_to_dict
from bs4 import BeautifulSoup, NavigableString
import copy
from flask import current_app
import html
import os
import urllib.parse as urlparse
from urllib.parse import parse_qs
import re
import warnings

SKIP_ARGS = ['ref_src', 'utm']
SKIP_PREFIX = ['//www.', '//mobile.', '//m.', 'www.', 'mobile.', 'm.']
GOOG_STATIC = 'www.gstatic.com'
G_M_LOGO_URL = 'https://www.gstatic.com/m/images/icons/googleg.gif'
GOOG_IMG = '/images/branding/searchlogo/1x/googlelogo'
LOGO_URL = GOOG_IMG + '_desk'
BLANK_B64 = ('data:image/png;base64,'
             'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAQAAAAnOwc2AAAAD0lEQVR42mNkw'
             'AIYh7IgAAVVAAuInjI5AAAAAElFTkSuQmCC')

# Ad keywords
BLACKLIST = [
    'ad', 'ads', 'anuncio', 'annuncio', 'annonce', 'Anzeige', '广告', '廣告',

import base64
from bs4 import BeautifulSoup as bsoup
from flask import Request
import hashlib
import io
import os
import re
from requests import exceptions, get
from urllib.parse import urlparse

ddg_favicon_site = 'http://icons.duckduckgo.com/ip2'

empty_gif = base64.b64decode(
    'R0lGODlhAQABAIAAAP///////yH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==')

placeholder_img = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAYAAADE6YVjAAABF0lEQVRIS8XWPw9EMBQA8Eok' \
    'JBKrMFqMBt//GzAYLTZ/VomExPDu6uLiaPteqVynBn0/75W2Vp7nEIYhe6p1XcespmmAd7Is' \
    'M+4URcGiKPogvMMvmIS2eN9MOMKbKWgf54SYgI4vKkTuQKJKSJErkKzUSkQHUs0lilAg7GMh' \
    'ISoIA/hYMiKCKIA2soeowCWEMkfHtUmrXLcyGYYBfN9HF8djiaglWzNZlgVs21YisoAUaEXG' \
    'cQTP86QIFgi7vyLzPIPjOEIEC7ANQv/4aZrAdd0TUtc1i+MYnSsMWjPp+x6CIPgJVlUVS5KE' \
    'DKig/+wnVzM4pnzaGeHd+ENlWbI0TbVLJBtw2uMfP63wc9d2kDCWxi5Q27bsBerSJ9afJbeL' \
    'AAAAAElFTkSuQmCC'
)


def fetch_favicon(url: str) -> bytes:
    """Fetches a favicon using DuckDuckGo's favicon retriever

    Args:
        url: The url to fetch the favicon from
    Returns:
        bytes - the favicon bytes, or a placeholder image if one
        was not returned
    """
    domain = urlparse(url).netloc

    response = get(f'{ddg_favicon_site}/{domain}.ico')

    if response.status_code == 200 and len(response.content) > 0:
        tmp_mem = io.BytesIO()
        tmp_mem.write(response.content)
        tmp_mem.seek(0)

        return tmp_mem.read()
    else:
        return placeholder_img


def gen_file_hash(path: str, static_file: str) -> str:
    file_contents = open(os.path.join(path, static_file), 'rb').read()
    file_hash = hashlib.md5(file_contents).hexdigest()[:8]
    filename_split = os.path.splitext(static_file)

    return filename_split[0] + '.' + file_hash + filename_split[-1]


def read_config_bool(var: str) -> bool:
    val = os.getenv(var, '0')
    # user can specify one of the following values as 'true' inputs (all
    # variants with upper case letters will also work):
    # ('true', 't', '1', 'yes', 'y')
    val = val.lower() in ('true', 't', '1', 'yes', 'y')
    return val


def get_client_ip(r: Request) -> str:
    if r.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return r.environ['REMOTE_ADDR']
    else:
        return r.environ['HTTP_X_FORWARDED_FOR']


def get_request_url(url: str) -> str:
    if os.getenv('HTTPS_ONLY', False):
        return url.replace('http://', 'https://', 1)

    return url


def get_proxy_host_url(r: Request, default: str, root=False) -> str:
    scheme = r.headers.get('X-Forwarded-Proto', 'https')
    http_host = r.headers.get('X-Forwarded-Host')

    full_path = r.full_path if not root else ''
    if full_path.startswith('/'):
        full_path = f'/{full_path}'

    if http_host:
        prefix = os.environ.get('WHOOGLE_URL_PREFIX', '')
        if prefix:
            prefix = f'/{re.sub("[^0-9a-zA-Z]+", "", prefix)}'
        return f'{scheme}://{http_host}{prefix}{full_path}'

    return default


def check_for_update(version_url: str, current: str) -> int:
    # Check for the latest version of Whoogle
    try:
        update = bsoup(get(version_url).text, 'html.parser')
        latest = update.select_one('[class="Link--primary"]').string[1:]
        current = int(''.join(filter(str.isdigit, current)))
        latest = int(''.join(filter(str.isdigit, latest)))
        has_update = '' if current >= latest else latest
    except (exceptions.ConnectionError, AttributeError):
        # Ignore failures, assume current version is up to date
        has_update = ''

    return has_update


def get_abs_url(url, page_url):
    # Creates a valid absolute URL using a partial or relative URL
    if url.startswith('//'):
        return f'https:{url}'
    elif url.startswith('/'):
        return f'{urlparse(page_url).netloc}{url}'
    elif url.startswith('./'):
        return f'{page_url}{url[2:]}'
    return url


def list_to_dict(lst: list) -> dict:
    if len(lst) < 2:
        return {}
    return {lst[i].replace(' ', ''): lst[i+1].replace(' ', '')
            for i in range(0, len(lst), 2)}

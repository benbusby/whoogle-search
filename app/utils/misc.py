from bs4 import BeautifulSoup as bsoup
from flask import Request
import hashlib
import os
from requests import exceptions, get
from urllib.parse import urlparse


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
    if http_host:
        return f'{scheme}://{http_host}{r.full_path if not root else "/"}'

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

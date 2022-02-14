from bs4 import BeautifulSoup as bsoup
from flask import Request
import hashlib
import os
from requests import exceptions, get


def gen_file_hash(path: str, static_file: str) -> str:
    file_contents = open(os.path.join(path, static_file), 'rb').read()
    file_hash = hashlib.md5(file_contents).hexdigest()[:8]
    filename_split = os.path.splitext(static_file)

    return filename_split[0] + '.' + file_hash + filename_split[-1]


def read_config_bool(var: str) -> bool:
    val = os.getenv(var, '0')
    if val.isdigit():
        return bool(int(val))
    return False


def get_client_ip(r: Request) -> str:
    if r.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return r.environ['REMOTE_ADDR']
    else:
        return r.environ['HTTP_X_FORWARDED_FOR']


def get_request_url(url: str) -> str:
    if os.getenv('HTTPS_ONLY', False):
        return url.replace('http://', 'https://', 1)

    return url


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

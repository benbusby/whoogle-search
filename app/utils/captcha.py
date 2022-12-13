import os

from bs4 import BeautifulSoup as bs
try:
    import deathbycaptcha
except ImportError:
    deathbycaptcha = None

def parse_params(response):
    params = {
        "googlekey":"",
        "data-s": "",
        "pageurl": ""
    }
    soup = bs(response)

def solve(response):
    if deathbycaptcha is None:
        raise ImportError("The deathbycaptcha client is not installed")

    client = deathbycaptcha.HttpClient(
        os.env.get("DBC_USER", "username"),
        os.env.get("DBC_PASS")
    )

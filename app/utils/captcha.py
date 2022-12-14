"""
Itegration with third party CAPTCHA solving services
"""
# only deathbycaptcha atm but whatever
import os

from bs4 import BeautifulSoup as bs

try:
    import deathbycaptcha
except ImportError:
    deathbycaptcha = None


class UnableToSolve(Exception):
    """
    The third-party service was unable to solve the CAPTCHA
    """


def parse_params(response):
    """
    Parses a page with bs4 to fetch the data needed to solve the captcha.
    """
    params = {
        "googlekey": "",
        "data-s": "",
        "pageurl": "",
    }
    soup = bs(response.text)

    recaptcha = soup.find(id="recaptcha")
    if not recaptcha:
        # i could save the page for debugging since this is usually
        # hard to reproduce
        raise AttributeError(
            "Couldn't find the element with the CAPTCHA params"
            "Are you sure this page contains Google's reCAPTCHA v2 with callback?"
        )
    params["googlekey"] = recaptcha.attrs["data-sitekey"]
    params["data-s"] = recaptcha.attrs["data-s"]

    params["pageurl"] = response.url

    return params


def solve(response):
    """
    Get a response with a reCAPTCHA v2 and solve it using a third-party service
    """
    if deathbycaptcha is None:
        raise ImportError("The deathbycaptcha client is not installed")

    client = deathbycaptcha.HttpClient(
        os.environ.get("DBC_USER", "username"), os.environ.get("DBC_PASS", "password")
    )

    params = parse_params(response)

    token = client.decode(type=4, token_params=params)
    if not token or token == "?":
        raise UnableToSolve("Deathbycaptcha was unable to solve the captcha")

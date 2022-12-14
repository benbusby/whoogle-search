"""
Itegration with third party CAPTCHA solving services
"""
# only deathbycaptcha atm but whatever
import os
import json
import requests

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
    hidden_q = soup.find(type="hidden")
    params["q"] = hidden_q.attrs["value"]
    params["googlekey"] = recaptcha.attrs["data-sitekey"]
    params["data-s"] = recaptcha.attrs["data-s"]

    return params


def solve(response, proxies, url):
    """
    Get a response with a reCAPTCHA v2 and solve it using a third-party service
    """
    if deathbycaptcha is None:
        print("WARN: The deathbycaptcha client is not installed")
        return False

    client = deathbycaptcha.HttpClient(
        os.environ.get("DBC_USER", "username"), os.environ.get("DBC_PASS", "password")
    )

    params = parse_params(response)
    params["pageurl"] = url
    params["proxy"] = proxies.get("https", None)
    params["proxytype"] = "HTTP"

    q = params.pop("q")

    token = ""
    try:
        token = client.decode(type=4, token_params=json.dumps(params))
    except Exception as exc:
        print(
            "ERROR: Deathbycaptcha was unable to solve the captcha. Original exception:", exc
        )
        return False

    if not token or token.get("is_correct", "false") == "false":
        print("ERROR: Deathbycaptcha was unable to solve the captcha")
        return False
    text = token.get("text", None)
    if text:
        form_params = {
            "q": q,
            "continue": url,
            "g-recaptcha-response": text,
        }
        response = requests.post("https://www.google.com/sorry/index", data=form_params, proxies=proxies)
        print(response, form_params, response.text)
        return True
    return False

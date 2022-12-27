"""
Test the integration with third-party CAPTCHA solving services
"""

from pathlib import Path
from argparse import Namespace

from app.utils import captcha

TEST_FILES = Path(__file__).parent / "test_files"


def test_parse():
    """
    Test the parsing functionality
    """

    with open(TEST_FILES / "recaptcha_v2_callback.html") as file:
        text = file.read()
    # primitive mock
    response = Namespace()
    response.url = "https://www.google.com/search?gbv=1&num=10&q=Liddell&safe=off"
    response.text = text

    res = captcha.parse_params(response)

    data_s = (
        "I_wQ5kiIMUbCdcGyC1x6zzK70nD"
        "G9kViGr7TS6zaiWsIdZXcmQGoaxN"
        "hiGulX8tD_xNYFXLRkLFSkxDnrkIr"
        "5o5xSw2Sj1Z-bs5dqP2TyQFGBaTZFY"
        "sRBy3CoDJruyranhLqWoWb3mdxvgUb"
        "kpS7ZkRSFYFP_dg9WV4rIQxa6OUmrAt"
        "S6JKw_UbHN8tJ4mCpz6BKYsGB_fjyD9"
        "fuRrzmn2RK8FzsOAiLEWBc0z5Qxdltd"
        "owqO1ugNxQdSaqM39pF73cCAqWqEama"
        "RRa9iOOVflHptIHjo88"
    )

    expected = {
        "googlekey": "6LfwuyUTAAAAAOAmoS0fdqijC2PbbdH4kjq62Y1b",
        "data-s": data_s,
        'q': 'EgTIadcWGIXS4pwGIjDL-1ocR_DlZgts3Rfama1w7aWKF_5y2vFWA8eORDe5SvseqGuuMVzIObjhBnZPpgAyAXI'
    }

    message = "Results differ\n" f"Expected: {expected}\n" f"Got: {res}"
    assert res == expected, message

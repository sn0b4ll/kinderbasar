"""Helper class so we dont have to do this in every module."""
import logging
import requests
import json

from configparser import ConfigParser
from argon2 import PasswordHasher

# Init logging
logging.basicConfig(  # TODO(Do only once -> own module)
    filename="./logs/kinderbasar.log",
    format="%(asctime)s:%(levelname)s:%(message)s",
    level=logging.DEBUG,
)

# Init config parser
config = ConfigParser()
config.read("./conf/env.conf")  # TODO(Do only once -> own module)

# Init the password hasher

ph = PasswordHasher()


def _filter_article_current(article):
    return article.current


def _filter_article_reactivated(article):
    return not article.reactivated

def is_human(captcha_response):
    """ Validating recaptcha response from google server
        Returns True captcha test passed for submitted form else returns False.
    """
    secret = config['APP']['recaptcha_secret_key']
    payload = {'response':captcha_response, 'secret':secret}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
    response_text = json.loads(response.text)
    return response_text['success']
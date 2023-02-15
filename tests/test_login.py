'''Test file dedicated to login related functions.'''
# pylint: disable=import-error

from configparser import ConfigParser

import pytest # pylint: disable=unused-import
import requests

# Init config parser
config = ConfigParser()
config.read('./conf/env.conf')

# Create a requests session
req_session = requests.Session()

def test_login():
    '''Is the login working?'''
    post_data = { # TODO(Config for test-data?)
        'username': 'seller1@kinderbasar-elsendorf.de',
        'password': 'test'
    }

    response = req_session.post(f"{ config['APP']['url'] }/login", data = post_data)
    assert response.status_code is 200
    assert 'logout' in response.text

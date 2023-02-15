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

def test_login_logout():
    '''Is the login working?'''
    post_data = { # TODO(Config for test-data?)
        'username': 'seller1@kinderbasar-elsendorf.de',
        'password': 'test'
    }

    response = req_session.post(f"{ config['APP']['url'] }/login", data = post_data)
    assert response.status_code is 200
    assert 'logout' in response.text

def test_logout():
    '''Is the login working?'''

    # Check if login is still there
    response = req_session.get(f"{ config['APP']['url'] }/overview")
    assert response.status_code is 200
    assert 'Artikel Übersicht' in response.text

    # Try to log out
    response = req_session.get(f"{ config['APP']['url'] }/logout")
    assert response.status_code is 200
    assert 'Login' in response.text

    # Try to call something after logging out
    response = req_session.get(f"{ config['APP']['url'] }/overview")
    assert response.status_code is 200
    assert 'Artikel Übersicht' not in response.text

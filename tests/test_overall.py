'''Test file dedicated to overall tests.'''
# pylint: disable=import-error

from configparser import ConfigParser

import pytest # pylint: disable=unused-import
import requests

# Init config parser
config = ConfigParser()
config.read('./conf/env.conf')

# Create a requests session
req_session = requests.Session()

def test_alive():
    '''Is the website alive?'''
    response = req_session.get(config['APP']['url'])
    assert response.status_code is 200
    assert 'login' in response.text
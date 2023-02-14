# pylint: import-error
import pytest
import requests

from configparser import ConfigParser

import os
print(os.getcwd())

# Init config parser
config = ConfigParser()
config.read('./conf/env.conf')

# Create a requests session
req_session = requests.Session()

# Login for the next tests
login_data = { # TODO(Config for test-data?)
    'username': 'seller1@kinderbasar-elsendorf.de',
    'password': 'test'
}
req_session.post(f"{ config['APP']['url'] }/login", data = login_data)

def test_article_add_page():
    '''Is the article add page loading?'''

    response = req_session.get(f"{ config['APP']['url'] }/article/add")
    assert response.status_code is 200
    assert 'Artikel hinzufügen' in response.text

def test_article_add_article():
    '''Is it possible to add an article?'''

    art_name = 'TEST NAME'
    art_price = '13,37'
    art_clothing_size = 'SIZE TEST'

    post_data = {
        'name': art_name,
        'price': art_price,
        'clothing_size': art_clothing_size
    }

    response = req_session.post(f"{ config['APP']['url'] }/article/add", data = post_data)
    assert response.status_code is 200
    assert 'Artikel Übersicht' in response.text
    assert art_name in response.text
    assert art_price in response.text
    assert art_clothing_size in response.text

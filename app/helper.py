"""Helper class so we dont have to do this in every module."""
import logging

from configparser import ConfigParser
from argon2 import PasswordHasher

# Init logging
logging.basicConfig( # TODO(Do only once -> own module)
    filename='./logs/kinderbasar.log', 
    format='%(asctime)s:%(levelname)s:%(message)s',
    level=logging.DEBUG
)

# Init config parser
config = ConfigParser()
config.read('./conf/env.conf') # TODO(Do only once -> own module)

# Init the password hasher

ph = PasswordHasher()

'''This module is responsible for creating test-data.'''
# pylint: disable=no-member

import uuid

from models import db
from models import  Article, User, Card

from argon2 import PasswordHasher
ph = PasswordHasher()

def create_test_data():
    '''Creates test-data.'''
    user = User()
    user.salt = str(uuid.uuid4())
    user.password = ph.hash("abcd"+user.salt)
    user.email = "testuser1@user.de"
    user.name = "testuser1"
    user.organizer = False
    user.activated = True
    user.registration_done = False
    db.session.add(user)

    user2 = User()
    user2.salt = str(uuid.uuid4())
    user2.password = ph.hash("abcd"+user.salt)
    user2.email = "testuser2@user.de"
    user2.name = "testuser2"
    user2.organizer = True
    user2.activated = True
    user2.registration_done = False
    db.session.add(user2)

    db.session.commit()

    article = Article()
    article.uuid = str(uuid.uuid4())
    article.name = "Testname"
    article.seller = user
    article.clothing_size = ""
    article.price = 1330
    article.sold = False
    db.session.add(article)

    article2 = Article()
    article2.uuid = str(uuid.uuid4())
    article2.name = "Testname2"
    article2.seller = user
    article2.clothing_size = "42"
    article2.price = 2450
    article2.sold = False
    db.session.add(article2)

    article3 = Article()
    article3.uuid = str(uuid.uuid4())
    article3.name = "Testname3"
    article3.seller = user2
    article3.clothing_size = "42"
    article3.price = 2450
    article3.sold = False
    db.session.add(article3)

    card = Card()
    card.uuid = str(uuid.uuid4())
    card.articles = [article, article2]
    card.active = True
    db.session.add(card)

    user2.cards = [card]

    db.session.commit()

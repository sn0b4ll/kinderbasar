'''This module is responsible for creating test-data.'''
# pylint: disable=no-member,import-error

import uuid

from models import db
from models import Article, User, Shoppingbasket

from helper import ph

# TODO (Move as constructors into models)
def _create_user(user_id, password, email, activated, organizer, checkin_done):
    '''Create an user.'''
    new_user = User()

    new_user.id = int(user_id)
    new_user.salt = str(uuid.uuid4())
    new_user.password = ph.hash(password+new_user.salt)
    new_user.email = email
    new_user.activation_code = None
    new_user.activated = activated
    new_user.organizer = organizer
    new_user.checkin_done = checkin_done

    db.session.add(new_user)

    return new_user, user_id + 1

def _create_article(user, name, price, clothing_size, current):
    '''Create a new article'''
    new_article = Article()

    new_article.uuid = str(uuid.uuid4())
    new_article.name = name
    new_article.price = price
    new_article.sold = False
    new_article.clothing_size = clothing_size
    new_article.current = current
    new_article.card_uuid = None
    new_article.seller = user

    db.session.add(new_article)

def _create_shoppingbasket(user):
    '''Create a new shopping basket and assign to user.'''
    new_basket = Shoppingbasket()
    new_basket.owner = user

    db.session.add(new_basket)

def create_test_data():
    '''Creates test-data.'''

    # Users
    ## Start the user ID counter at 1
    user_id = 1

    ## Org Users
    user_admin, user_id = _create_user(user_id, 'test', 'admin@kinderbasar-elsendorf.de', True, True, False)
    user_kasse1, user_id = _create_user(user_id, 'test', 'kasse1@kinderbasar-elsendorf.de', True, True, False)
    user_kasse2, user_id = _create_user(user_id, 'test', 'kasse2@kinderbasar-elsendorf.de', True, True, False)
    user_kasse3, user_id = _create_user(user_id, 'test', 'kasse3@kinderbasar-elsendorf.de', True, True, False)

    ## Sellers
    user_seller1, user_id = _create_user(user_id, 'test', 'seller1@kinderbasar-elsendorf.de', True, False, False)
    user_seller2, user_id = _create_user(user_id, 'test', 'seller2@kinderbasar-elsendorf.de', True, False, False)
    user_seller3, user_id = _create_user(user_id, 'test', 'seller3@kinderbasar-elsendorf.de', True, False, False)
    user_seller4, user_id = _create_user(user_id, 'test', 'seller4@kinderbasar-elsendorf.de', True, False, False)

    ## Commit the users
    db.session.commit()

    # Articles
    ## Create Articles for every user
    _create_article(user_seller1, "Test-Art 1", 2000, 'XL', True)
    _create_article(user_seller1, "Test-Art 2", 2500, 'L', True)
    _create_article(user_seller1, "Test-Art 3", 500, '', True)
    _create_article(user_seller1, "Test-Art 4", 12000, 'ASDASDASD', True)
    _create_article(user_seller1, "Test-Art 5", 1250, 'XL', False)
    _create_article(user_seller1, "Test-Art 6", 1000, '', False)

    _create_article(user_seller2, "Test-Art 7", 2000, 'XL', True)
    _create_article(user_seller2, "Test-Art 8", 2500, 'L', True)
    _create_article(user_seller2, "Test-Art 9", 500, '', True)
    _create_article(user_seller2, "Test-Art 10", 12000, 'ASDASDASD', True)
    _create_article(user_seller2, "Test-Art 11", 1250, 'XL', False)
    _create_article(user_seller2, "Test-Art 12", 1000, '', False)

    _create_article(user_seller3, "Test-Art 13", 100, 'XL', False)
    _create_article(user_seller3, "Test-Art 14", 10000, '', False)

    _create_article(user_seller4, "Test-Art 14", 100, '', True)
    _create_article(user_seller4, "Test-Art 15", 1000, '', True)

    ## Commit the users
    db.session.commit()

    # Shopping Baskets
    ## Create the baskets
    _create_shoppingbasket(user_seller1)
    _create_shoppingbasket(user_seller1)
    _create_shoppingbasket(user_seller2)
    _create_shoppingbasket(user_seller3)
    _create_shoppingbasket(user_seller3)
    _create_shoppingbasket(user_seller3)
    _create_shoppingbasket(user_seller3)
    _create_shoppingbasket(user_seller3)

    ## Aaaaand commit them
    db.session.commit()


"""Imports old data from json into the new db."""
# pylint: disable=no-member,logging-fstring-interpolation,import-error
import json
import logging

from datetime import datetime

from models import Article, User
from models import db

# Init logging
logging.basicConfig(
    filename='./logs/kinderbasar.log', 
    format='%(asctime)s:%(levelname)s:%(message)s', 
    level=logging.INFO
)

USER_JSON_PATH = "app/utils/db_migration_files/user.json"
ARTICLE_JSON_PATH = "app/utils/db_migration_files/article.json"

def _create_user(user_id, password, salt, email, activated, organizer):
    new_user = User()

    new_user.id = int(user_id)
    new_user.password = password
    new_user.salt = salt
    new_user.email = email
    new_user.activation_code = None
    new_user.activated = bool(int(activated))
    new_user.organizer = bool(int(organizer))
    new_user.checkin_done = False

    db.session.add(new_user)

def _create_article(uuid, name, price, clothing_size, user_id):
    new_article = Article()

    new_article.uuid = uuid
    new_article.name = name
    new_article.price = price
    new_article.sold = False
    new_article.clothing_size = clothing_size
    new_article.reactivated = False
    new_article.current = False
    new_article.last_current = datetime(2022, 10, 1)

    new_article.card_uuid = None

    # Set correct selling user
    new_article.seller = db.session.get(User, user_id)

    db.session.add(new_article)

def _remove_users_without_articles():
    '''Remove all users without articles.'''

    user_list = db.session.query(User).all()
    for us in user_list:
        if len(us.articles) == 0:
            logging.info(f"Found { us.id } with 0 articles.")
            db.session.delete(us)
        else:
            logging.info(f"Found { us.id } with { len(us.articles) } articles.")

def migrate_data():
    '''Main function to migrate data.'''
    logging.info('[+] Starting data migration.')
    with open(USER_JSON_PATH, encoding='utf-8') as user_file:
        data = json.load(user_file)

    for user in data:
        _create_user(
            user['id'],
            user['password'],
            user['salt'],
            user['email'],
            user['activated'],
            user['organizer']
        )

    db.session.commit()
    logging.info('[+] Finished with users, switiching to articles.')

    with open(ARTICLE_JSON_PATH, encoding='utf-8') as article_file:
        data = json.load(article_file)
    cnt = len(data)
    cur = 0
    logging.info('[+] Got here (before migrate).')
    for art in data:
        logging.info(f"[+] Migrating Art { cur }/{ cnt }")
        if not art['sold'] == '1':
            _create_article(
                art['uuid'],
                art['name'],
                int(art['price']),
                art['clothing_size'],
                int(art['user_id'])
            )
        cur += 1

    db.session.commit()
    logging.info('[+] Finished with articles, cleaing up DB.')

    _remove_users_without_articles()
    db.session.commit()

    logging.info('[+] Migration done.')

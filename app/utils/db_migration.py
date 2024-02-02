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

def _migrate_users():
    '''Clean up and prepare users for new basar'''

    user_list = db.session.query(User).all()
    for us in user_list:
        # Remove user if no articles were offered and it is not an organizer
        if len(us.articles) == 0 and not us.organizer:
            logging.info(f"Found { us.id } with 0 articles.")
            db.session.delete(us)
        
        # Reset field field
        us.registration_done = False
        us.checkin_done = False


def _migrate_articles():
    '''Clean up and prepare articles for new basar'''

    article_list = db.session.query(Article).all()
    for article in article_list:
        if article.sold:
            db.session.delete(article)
        else:
            article.current = False
            article.reactivated = False
            

def migrate_data():
    '''Main function to migrate data.'''

    logging.info('[+] Starting data migration.')

    # Migrate users
    logging.info('[+] Migrating users.')
    _migrate_users()

    # Remove sold articles and set date for articles
    logging.info('[+] Migrating articles.')
    _migrate_articles()

    db.session.commit()
    logging.info('[+] Migration done.')

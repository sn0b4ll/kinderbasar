"""Imports old data from json into the new db. This is to be enabled from run.py"""

# pylint: disable=no-member,logging-fstring-interpolation,import-error
import logging

from models import Article, User, Cart
from models import db

# Init logging
logging.basicConfig(
    filename="./logs/kinderbasar.log",
    format="%(asctime)s:%(levelname)s:%(message)s",
    level=logging.INFO,
)


def _migrate_users():
    """Clean up and prepare users for new basar"""
    logging.info("Cleaning up users")
    user_list = db.session.query(User).all()
    for user in user_list:
        # Remove user if no articles were offered and it is not an organizer
        if len(user.articles) == 0 and not user.organizer:
            logging.info(f"Found { user.id } with 0 articles.")
            db.session.delete(user)
        else:
            # Reset fields
            user.checkin_done = False
            db.session.add(user)


def _migrate_articles():
    """Clean up and prepare articles for new basar"""
    logging.info("Cleaning up articles")
    article_list = db.session.query(Article).all()
    for article in article_list:
        if article.sold:
            db.session.delete(article)
        else:
            article.current = False
            article.reactivated = False
            db.session.add(article)


def _migrate_carts():
    """Clean up and prepare carts for new basar"""
    logging.info("Cleaning up carts")
    cart_list = db.session.query(Cart).all()
    for cart in cart_list:
        db.session.delete(cart)


def migrate_data():
    """Main function to migrate data."""

    logging.info("[+] Starting data migration.")

    # Migrate users
    logging.info("[+] Migrating users.")
    _migrate_users()

    # Remove sold articles and set date for articles
    logging.info("[+] Migrating articles.")
    _migrate_articles()

    # Remove old carts
    logging.info("[+] Clean carts.")
    _migrate_carts()

    db.session.commit()
    logging.info("[+] Migration done.")

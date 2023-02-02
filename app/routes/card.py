'''Serves pages linked to the card handling.'''
# pylint: disable=no-member,logging-fstring-interpolation

import uuid
import logging
import math

from configparser import ConfigParser

from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import session

from models import db
from models import Article, User, Card

# Init config parser
config = ConfigParser()
config.read('./conf/env.conf') # TODO(Do only once -> own module)

# Init logging
logging.basicConfig( # TODO(Do only once -> own module)
    filename='./logs/kinderbasar.log', 
    format='%(asctime)s:%(levelname)s:%(message)s', 
    level=logging.DEBUG
)

card_handling = Blueprint('card_handling', __name__, template_folder='templates')


def _get_card_uuid_for_user():
    user = User.query.get(session['user_id'])
    for card in user.cards:
        if card.active:
            return card.uuid

    # No active card, create one
    card = Card()
    card.uuid = str(uuid.uuid4())
    card.articles = []
    card.active = True
    card.user_id = user.id
    db.session.add(card)

    db.session.commit()

    return card.uuid

@card_handling.route("/card/<string:uuid>/", methods=["GET"])
def card(uuid):
    '''Display a card. '''
    if ('organizer' in session) and (session['organizer'] == True) :
        if uuid == "active":
            uuid = _get_card_uuid_for_user()

        card = Card.query.get(uuid)

        if card is None:
            return "Card not found."

        if card.user_id != session['user_id']:
            return "Wrong Session!"

        price_overall = 0
        for article in card.articles:
            price_overall += int(article.price)

        seller_margin = int(price_overall * 0.05)
        total_price = price_overall + seller_margin
        total_price_rounded = math.ceil(total_price/10)*10

        return render_template(
                'card.html',
                card=card,
                price_overall=price_overall,
                seller_margin=seller_margin,
                total_price=total_price,
                total_price_rounded=total_price_rounded,
                org=True
            )
    else:
        return redirect(url_for('login'))

@card_handling.route("/card/<string:card_uuid>/add/<string:article_uuid>/", methods=["POST"])
def add_article_to_card(card_uuid, article_uuid):
    '''Adds an article to an card, both identified by uuid.'''
    if ('organizer' in session) and (session['organizer'] == True) :
        if card_uuid == "active":
            card_uuid = _get_card_uuid_for_user()

        card = Card.query.get(card_uuid)

        if card is None:
            return "Card not found."

        if card.user_id != session['user_id']:
            return "Wrong Session!"

        article = Article.query.get(article_uuid)

        if article is None:
            return "Article UUID wrong!"

        card.articles.append(article)
        db.session.commit()

        price_overall = 0
        for article in card.articles:
            price_overall += int(article.price)

        seller_margin = int(price_overall * 0.05)
        total_price = price_overall + seller_margin
        total_price_rounded = math.ceil(total_price/10)*10

        return render_template(
                'card.html',
                card=card,
                price_overall=price_overall,
                seller_margin=seller_margin,
                total_price=total_price,
                total_price_rounded=total_price_rounded,
                org=True
            )
    else:
        return redirect(url_for('login'))

@card_handling.route("/card/<string:uuid>/close/", methods=["POST"])
def close_card(uuid):
    '''Closes a card.'''
    if ('organizer' in session) and (session['organizer'] == True) :
        if uuid == "active":
            uuid = _get_card_uuid_for_user()

        current_card = Card.query.get(uuid)

        if current_card is None:
            return "Card not found."

        if current_card.user_id != session['user_id']:
            return "Wrong Session!"

        current_card.active = False

        for article in current_card.articles:
            article.sold = True

        db.session.commit()

        logging.info(f"The card {uuid} was closed.")

        price_overall = 0
        for article in current_card.articles:
            price_overall += int(article.price)

        seller_margin = int(price_overall * 0.05)
        total_price = price_overall + seller_margin
        total_price_rounded = math.ceil(total_price/10)*10

        return render_template(
                'card.html',
                card=current_card,
                price_overall=price_overall,
                seller_margin=seller_margin,
                total_price=total_price,
                total_price_rounded=total_price_rounded,
                org=True
            )
    else:
        return redirect(url_for('login'))

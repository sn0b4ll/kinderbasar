"""Serves pages linked to the card handling."""
# pylint: disable=no-member,logging-fstring-interpolation,import-error

import uuid
import math

from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import session

from models import db
from models import Article, User, Card

from helper import logging

card_handling = Blueprint("card_handling", __name__, template_folder="templates")


def _get_card_uuid_for_user():
    user = User.query.get(session["user_id"])
    for cur_card in user.cards:
        if cur_card.active:
            return cur_card.uuid

    # No active card, create one
    cur_card = Card()
    cur_card.uuid = str(uuid.uuid4())
    cur_card.articles = []
    cur_card.active = True
    cur_card.user_id = user.id
    db.session.add(cur_card)

    db.session.commit()

    return cur_card.uuid


@card_handling.route("/card/<string:card_uuid>/", methods=["GET"])
def card(card_uuid):
    """Display a card."""
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user.organizer:
            if card_uuid == "active":
                card_uuid = _get_card_uuid_for_user()

            current_card = Card.query.get(card_uuid)

            if current_card is None:
                return "Card not found."

            if current_card.user_id != session["user_id"]:
                return "Wrong Session!"

            price_overall = 0
            for article in current_card.articles:
                price_overall += int(article.price)

            seller_margin = int(price_overall * 0.05)
            total_price = price_overall + seller_margin
            total_price_rounded = math.ceil(total_price / 10) * 10

            return render_template(
                "card.html",
                card=current_card,
                price_overall=price_overall,
                seller_margin=seller_margin,
                total_price=total_price,
                total_price_rounded=total_price_rounded,
                org=True,
            )

    return redirect(url_for("session_handling.login"))


@card_handling.route(
    "/card/<string:card_uuid>/add/<string:article_uuid>/", methods=["POST"]
)
def add_article_to_card(card_uuid, article_uuid):
    """Adds an article to an card, both identified by uuid."""
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user.organizer:
            if card_uuid == "active":
                card_uuid = _get_card_uuid_for_user()

            current_card = Card.query.get(card_uuid)

            if current_card is None:
                return "Card not found."

            if current_card.user_id != session["user_id"]:
                return "Wrong Session!"

            article = Article.query.get(article_uuid)

            if article is None:
                return "Article UUID wrong!"

            if not article.current:
                return "Article was not actived for current basar!"

            current_card.articles.append(article)
            db.session.commit()

            price_overall = 0
            for article in current_card.articles:
                price_overall += int(article.price)

            seller_margin = int(price_overall * 0.05)
            total_price = price_overall + seller_margin
            total_price_rounded = math.ceil(total_price / 10) * 10

            return render_template(
                "card.html",
                card=current_card,
                price_overall=price_overall,
                seller_margin=seller_margin,
                total_price=total_price,
                total_price_rounded=total_price_rounded,
                org=True,
            )

    # Someone tried to add an article to a card without beeing an org, send him to login page.
    return redirect(url_for("session_handling.login"))


@card_handling.route("/card/<string:card_uuid>/close/", methods=["POST"])
def close_card(card_uuid):
    """Closes a card."""

    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user.organizer:
            if card_uuid == "active":
                card_uuid = _get_card_uuid_for_user()

            current_card = Card.query.get(card_uuid)

            if current_card is None:
                return "Card not found."

            if current_card.user_id != session["user_id"]:
                return "Wrong Session!"

            current_card.active = False

            for article in current_card.articles:
                article.sold = True

                # If an article was NOT added to the current basar, money goes to org
                # Assumption: User ID 1 has been created as an organizer
                if not article.current:
                    article.seller = User.query.get(1)
                    article.current = True

            db.session.commit()

            logging.info(f"The card {card_uuid} was closed.")

            price_overall = 0
            for article in current_card.articles:
                price_overall += int(article.price)

            seller_margin = int(price_overall * 0.05)
            total_price = price_overall + seller_margin
            total_price_rounded = math.ceil(total_price / 10) * 10

            return render_template(
                "card.html",
                card=current_card,
                price_overall=price_overall,
                seller_margin=seller_margin,
                total_price=total_price,
                total_price_rounded=total_price_rounded,
                org=True,
            )

    # Someone tried to close a card without beeing an organizer.
    return redirect(url_for("session_handling.login"))

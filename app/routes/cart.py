"""Serves pages linked to the cart handling."""
# pylint: disable=no-member,logging-fstring-interpolation,import-error

import uuid
import math

from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import session

from models import db
from models import Article, User, Cart

from helper import logging

cart_handling = Blueprint("cart_handling", __name__, template_folder="templates")


def _get_cart_uuid_for_user():
    user = User.query.get(session["user_id"])
    for cur_cart in user.carts:
        if cur_cart.active:
            return cur_cart.uuid

    # No active cart, create one
    cur_cart = Cart()
    cur_cart.uuid = str(uuid.uuid4())
    cur_cart.articles = []
    cur_cart.active = True
    cur_cart.user_id = user.id
    db.session.add(cur_cart)

    db.session.commit()

    return cur_cart.uuid


@cart_handling.route("/cart/<string:cart_uuid>/", methods=["GET"])
def cart(cart_uuid):
    """Display a cart."""
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user.organizer:
            if cart_uuid == "active":
                cart_uuid = _get_cart_uuid_for_user()

            current_cart = Cart.query.get(cart_uuid)

            if current_cart is None:
                return "cart not found."

            if current_cart.user_id != session["user_id"]:
                return "Wrong Session!"

            price_overall = 0
            for article in current_cart.articles:
                price_overall += int(article.price)

            seller_margin = int(price_overall * 0.05)
            total_price = price_overall + seller_margin
            total_price_rounded = math.ceil(total_price / 10) * 10

            return render_template(
                "org/cashdesk/cart.html",
                cart=current_cart,
                price_overall=price_overall,
                seller_margin=seller_margin,
                total_price=total_price,
                total_price_rounded=total_price_rounded,
                user=user
            )

    return redirect(url_for("session_handling.login"))


@cart_handling.route(
    "/cart/<string:cart_uuid>/add/<string:article_uuid>/", methods=["POST"]
)
def add_article_to_cart(cart_uuid, article_uuid):
    """Adds an article to an cart, both identified by uuid."""
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user.organizer:
            if cart_uuid == "active":
                cart_uuid = _get_cart_uuid_for_user()

            current_cart = Cart.query.get(cart_uuid)

            if current_cart is None:
                return "cart not found."

            if current_cart.user_id != session["user_id"]:
                return "Wrong Session!"

            article = Article.query.get(article_uuid)

            if article is None:
                return "Article UUID wrong!"

            if not article.current:
                return "Article was not actived for current basar!"

            current_cart.articles.append(article)
            db.session.commit()

            price_overall = 0
            for article in current_cart.articles:
                price_overall += int(article.price)

            seller_margin = int(price_overall * 0.05)
            total_price = price_overall + seller_margin
            total_price_rounded = math.ceil(total_price / 10) * 10

            return render_template(
                "org/cashdesk/cart.html",
                cart=current_cart,
                price_overall=price_overall,
                seller_margin=seller_margin,
                total_price=total_price,
                total_price_rounded=total_price_rounded,
                user=user
            )

    # Someone tried to add an article to a cart without being an org, send him to login page.
    return redirect(url_for("session_handling.login"))


@cart_handling.route("/cart/<string:cart_uuid>/close/", methods=["POST"])
def close_cart(cart_uuid):
    """Closes a cart."""

    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user.organizer:
            if cart_uuid == "active":
                cart_uuid = _get_cart_uuid_for_user()

            current_cart = Cart.query.get(cart_uuid)

            if current_cart is None:
                return "cart not found."

            if current_cart.user_id != session["user_id"]:
                return "Wrong Session!"

            current_cart.active = False

            for article in current_cart.articles:
                article.sold = True

                # If an article was NOT added to the current basar, money goes to org
                # Assumption: User ID 1 has been created as an organizer
                if not article.current:
                    article.seller = User.query.get(1)
                    article.current = True

            db.session.commit()

            logging.info(f"The cart {cart_uuid} was closed.")

            price_overall = 0
            for article in current_cart.articles:
                price_overall += int(article.price)

            seller_margin = int(price_overall * 0.05)
            total_price = price_overall + seller_margin
            total_price_rounded = math.ceil(total_price / 10) * 10

            return render_template(
                "org/cashdesk/cart.html",
                cart=current_cart,
                price_overall=price_overall,
                seller_margin=seller_margin,
                total_price=total_price,
                total_price_rounded=total_price_rounded,
                user=user
            )

    # Someone tried to close a cart without being an organizer.
    return redirect(url_for("session_handling.login"))

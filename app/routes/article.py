"""Serves pages linked to the article handling."""
# pylint: disable=no-member,logging-fstring-interpolation,import-error

import uuid

from datetime import datetime

from flask import Blueprint, Response
from flask import render_template, redirect, url_for, abort
from flask import request, session

from models import db
from models import Article, User, ARTICLE_COMMENT_SIZE, ARTICLE_NAME_SIZE

from helper import logging

article_handling = Blueprint("article_handling", __name__, template_folder="templates")


@article_handling.route("/article/add", methods=["GET", "POST"])
def add_article():
    """Display the page for adding an article or create one."""
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        if user.registration_done:
            return "Registration already finished.", 403

        if request.method == "GET":
            # Get request, return the form
            return render_template(
                "article/add_article.html", title="Add an article", user=user
            )

        # Post-Request, create an article
        name = request.form["name"][:ARTICLE_NAME_SIZE]
        price = request.form["price"]
        try:
            price = price.replace(",", "")
            price = price.replace("€", "")
            price = price.replace(".", "")
            price = int(price)
        except ValueError:
            return "Bitte beachten Sie die Vorgaben zur Preiseingabe. Sie erreichen die vorherige Seite über den Zurück-Button Ihres Browsers."

        comment = request.form["comment"][:ARTICLE_COMMENT_SIZE]

        article = Article()
        article.uuid = str(uuid.uuid4())
        article.name = name
        article.seller = User.query.get(session["user_id"])
        article.comment = comment
        article.current = True
        article.reactivated = False
        article.last_current = datetime.now()
        article.price = price
        article.sold = False

        db.session.add(article)
        db.session.commit()

        logging.info(f"Article {article.uuid}/{article.name} was created.")
        return redirect(url_for("overview"))

    return redirect(url_for("session_handling.login"))


@article_handling.route("/article/<string:art_uuid>", methods=["GET"])
def article_view(art_uuid):
    """Return the view for a single article."""
    if art_uuid is None:
        logging.debug(f"There was a try to access an not existing article {art_uuid}.")
        return abort(Response("Article UUID missing."))

    try:
        user = User.query.get(session["user_id"])
    except KeyError:
        # Anonymous user
        user = None

    article = Article.query.filter_by(uuid=art_uuid).first()

    return render_template("article/article.html", article=article, user=user)


@article_handling.route(
    "/article/<string:article_uuid>/reactivate", methods=["GET", "POST"]
)
def reactivate_article(article_uuid):
    """Reactivate an article from an previous basar."""
    if "user_id" in session:
        if article_uuid is None:
            return abort(Response("Article UUID missing."))

        user = User.query.get(session["user_id"])
        article = Article.query.get(article_uuid)

        if article in user.articles:
            article.current = True
            article.reactivated = True
            article.last_current = datetime.now()
        elif user.id == 1:
            article.current = True
            article.reactivated = True
            article.last_current = datetime.now()
            article.user_id = user.id
        else:
            return abort(Response("Article not linked to user."))

        db.session.commit()

        return redirect(url_for("overview"))

    return abort(Response("Please login to use this functionality."))


@article_handling.route("/article/<string:art_uuid>/remove", methods=["GET", "POST"])
def remove_article(art_uuid):
    """Permanently remove an article."""
    if "user_id" in session:
        if art_uuid is None:
            return abort(Response("Article UUID missing."))

        user = User.query.get(session["user_id"])
        article = Article.query.get(art_uuid)

        if (article not in user.articles) or user.registration_done or article.sold:
            logging.error(
                f"User {user.id } tried to delete article {art_uuid} but is not allowed to."
            )
            return "Not allowed to delete article.", 403

        db.session.delete(article)
        db.session.commit()

        logging.info(f"Article with UUID {art_uuid} was removed.")

        return redirect(url_for("overview"))

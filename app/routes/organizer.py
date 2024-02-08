"""Serves pages linked to organizer functions."""
# pylint: disable=no-member,logging-fstring-interpolation,import-error

import pdfkit  # pylint: disable=import-error # type: ignore
import uuid

from flask import Blueprint, Response
from flask import render_template, redirect, url_for
from flask import session, request

from models import db
from models import User, Article

from helper import logging, _filter_article_current, ph, config

organization_routes = Blueprint(
    "organization_routes", __name__, template_folder="templates"
)


@organization_routes.route("/org/checkin/<int:user_id>/", methods=["GET"])
def get_checkin(user_id):
    """Create the checking information."""

    loggedin_user = User.query.get(session["user_id"])
    if loggedin_user.organizer:
        user = db.session.get(User, user_id)
        articles_over = []
        articles_under = []

        provision = 0

        for article in filter(_filter_article_current, user.articles):
            # Calculate provision
            if article.price < 5000:
                provision += article.price * 0.05
            else:
                provision += 250

            # Depending on price, sort into under or over
            if article.price < 1000:
                articles_under.append(article)
            else:
                articles_over.append(article)

        return render_template(
            "checkin.html",
            user=user,
            articles_under=articles_under,
            articles_over=articles_over,
            provision=provision,
            org=True,
        )

    logging.info("Someone tried to navigate the login page without being an org.")
    return redirect(url_for("session_handling.login"))


@organization_routes.route("/org/checkin/done/<int:user_id>/", methods=["POST"])
def set_checkin(user_id):
    """Create the checking information."""
    loggedin_user = User.query.get(session["user_id"])
    if loggedin_user.organizer:
        user = db.session.get(User, user_id)
        user.checkin_done = True
        user.registration_done = True
        db.session.commit()

        logging.info(f"Checking for user {user_id} was closed.")

        return redirect(url_for("organization_routes.return_checking_page"))

    logging.info("Someone without org right tried to do a checkin.")
    return redirect(url_for("session_handling.login"))


@organization_routes.route("/sellers/", methods=["GET"])
def get_sellers():
    """List all sellers with their sold / unsold product count."""

    try:
        loggedin_user = User.query.get(session["user_id"])
    except KeyError:
        logging.info("Someone without org right tried access the sellers list.")
        return redirect(url_for("session_handling.login"))

    if loggedin_user.organizer:
        all_users = User.query.all()

        num_sellers = len(all_users)
        num_already_checkedin = 0
        sum_articles_current = 0

        seller_list = []
        for user in all_users:
            articles = list(filter(_filter_article_current, user.articles))
            articles_overall = len(articles)
            sum_articles_current += articles_overall
            articles_sold = 0
            for article in articles:
                if article.sold is True:
                    articles_sold += 1

            if user.checkin_done:
                num_already_checkedin += 1

            seller_list.append(
                (user, articles_overall, articles_sold, user.checkin_done)
            )

        return render_template(
            "sellers.html",
            seller_list=seller_list,
            num_sellers=num_sellers,
            num_already_checkedin=num_already_checkedin,
            sum_articles_current=sum_articles_current,
            org=True,
        )

    logging.info("Someone without org right tried access the sellers list.")
    return redirect(url_for("session_handling.login"))


@organization_routes.route("/org/checkin/", methods=["GET"])
def return_checking_page():
    """List all sellers for checkin."""

    try:
        loggedin_user = User.query.get(session["user_id"])
    except KeyError:
        logging.info("Someone without org right tried access the checkin list.")
        return redirect(url_for("session_handling.login"))

    if loggedin_user.organizer:
        registered_users = (
            db.session.query(User)
            .filter(User.registration_done, User.checkin_done is False)
            .all()
        )
        logging.info(len(registered_users))
        num_already_checkedin = len(
            db.session.query(User)
            .filter(User.registration_done, User.checkin_done)
            .all()
        )
        num_sellers = len(db.session.query(User).filter(User.registration_done).all())

        return render_template(
            "checkin_list.html",
            users=registered_users,
            num_sellers=num_sellers,
            num_already_checkedin=num_already_checkedin,
            org=True,
        )

    logging.info("Someone without org right tried access the checkin list.")
    return redirect(url_for("session_handling.login"))


@organization_routes.route("/org/stats/", methods=["GET"])
def return_stats_page():
    """List current stats."""

    try:
        loggedin_user = User.query.get(session["user_id"])
    except KeyError:
        logging.info("Someone without org right tried access the stats page.")
        return redirect(url_for("session_handling.login"))

    if loggedin_user.organizer:
        # Get the articles. Iterate over them, collecting the user_ids. Convert it into a list
        # using "list", make it unique with "set" and afterwards check the count with len
        articles = db.session.query(Article).filter(Article.current).all()
        num_sellers_with_articles = len(set(list((o.user_id for o in articles))))

        sum_articles_current = len(
            db.session.query(Article).filter(Article.current).all()
        )
        num_already_checkedin = len(
            db.session.query(User)
            .filter(User.registration_done, User.checkin_done)
            .all()
        )
        num_already_registered = len(
            db.session.query(User).filter(User.registration_done).all()
        )

        sum_articles_sold = len(
            db.session.query(Article).filter(Article.current, Article.sold).all()
        )

        return render_template(
            "stats.html",
            num_sellers_with_articles=num_sellers_with_articles,
            sum_articles_current=sum_articles_current,
            sum_articles_sold=sum_articles_sold,
            num_already_checkedin=num_already_checkedin,
            num_already_registered=num_already_registered,
            org=True,
        )

    logging.info("Someone without org right tried access the checkin list.")
    return redirect(url_for("session_handling.login"))


@organization_routes.route("/clearing/<int:user_id>/", methods=["GET"])
def get_clearing(user_id):
    """Get the final clearing document for a user after the basar ended."""
    if ("organizer" in session) and (session["organizer"] is True):
        user = db.session.get(User, user_id)
        articles = list(filter(_filter_article_current, user.articles))

        articles_unsold_abv10 = []

        sold_sum = 0
        for article in articles:
            if article.sold is True:
                sold_sum += article.price
            elif article.price >= 1000:
                articles_unsold_abv10.append(article)

        return render_template(
            "clearing.html",
            user=user,
            articles_unsold=articles_unsold_abv10,
            sold_sum=sold_sum,
        )

    logging.info("Someone without org right tried access the clearing for an seller.")
    return redirect(url_for("overview"))


@organization_routes.route("/clearing/printall", methods=["GET"])
def print_all_clearings():
    """Create a pdf holding all clearings for all users."""
    loggedin_user = User.query.get(session["user_id"])
    if loggedin_user.organizer:
        users = db.session.query(User).all()

        user_dict = {}
        user_with_current_articles = []

        for user in users:
            articles = list(filter(_filter_article_current, user.articles))

            # Skip for sellers with 0 current articles
            if len(articles) == 0:
                continue

            user_with_current_articles.append(user)
            articles_unsold_abv10 = []
            sold_sum = 0

            for article in articles:
                if article.sold is True:
                    sold_sum += article.price
                elif article.price >= 1000:
                    articles_unsold_abv10.append(article)

            user_dict[user] = {"articles": articles_unsold_abv10, "sold_sum": sold_sum}

        html = render_template(
            "clearing_all.html", users=user_with_current_articles, user_dict=user_dict
        )

        options = {
            "page-height": "297mm",
            "page-width": "210mm",
        }

        return Response(
            pdfkit.from_string(html, options=options),
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment;filename=clearing.pdf"},
        )

    logging.info("Someone without the right tried access the clearing for an seller.")
    return redirect(url_for("session_handling.login"))


@organization_routes.route("/user/<int:user_id>/unregister", methods=["GET"])
def user_unregister(user_id):
    """Unregister an user."""
    loggedin_user = User.query.get(session["user_id"])
    if loggedin_user.organizer:
        user = db.session.get(User, user_id)
        user.registration_done = False
        user.checkin_done = False
        db.session.commit()

        logging.info(
            f"Organizer with id { loggedin_user.id } unregistered user { user.id }."
        )
        return redirect(url_for("organization_routes.get_sellers"))

    logging.info("Someone without the right tried access the clearing for an seller.")
    return redirect(url_for("session_handling.login"))


@organization_routes.route("/org/resetpw", methods=["POST"])
def reset_pw():
    """Reset a PW for an E-Mail adress"""

    loggedin_user = User.query.get(session["user_id"])
    if loggedin_user.email == config["APP"]["admin_email"]:
        req_json = request.json
        email = req_json.get("email")

        user = db.session.query(User).filter(User.email == email).first()

        salt = str(uuid.uuid4())
        pass_hash = ph.hash(req_json.get("password") + salt)
        user.password = pass_hash
        user.salt = salt

        logging.info(f"Password for user {user.id}/{user.email} was changed.")

        db.session.add(user)
        db.session.commit()

        return Response(status=201)

    logging.warning("Someone tried to reset a password without being organizer.")
    return Response(status=401)

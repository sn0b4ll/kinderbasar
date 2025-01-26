"""Serves pages linked to checkin functions."""
# pylint: disable=no-member,logging-fstring-interpolation,import-error

from flask import Blueprint, redirect, render_template, session, url_for, request, abort, Response
from helper import _filter_article_current, logging
from models import User, db, CHECKIN_COMMENT_SIZE, Article

checkin_routes = Blueprint("checkin_routes", __name__, template_folder="templates")


@checkin_routes.route("/org/checkin/", methods=["GET"])
def return_checking_page():
    """List all sellers with current articles for checkin."""

    try:
        current_user = User.query.get(session["user_id"])
    except KeyError:
        logging.info("Someone without org right tried access the checkin list.")
        return redirect(url_for("session_handling.login"))

    if current_user.organizer:
        all_users = db.session.query(User).all()

        current_sellers = []
        remaining_sellers = []
        checkedin_sellers = []

        for user in all_users:
            if user.checkin_done:
                # If the user is already checked in, we don't have to
                # check anything else
                checkedin_sellers.append(user)
                current_sellers.append(user)
                continue
            
            for article in user.articles:
                if article.current:
                    remaining_sellers.append(user)
                    current_sellers.append(user)
                    break
    

        return render_template(
            "org/checkin/checkin_list.html",
            remaining_users=remaining_sellers,
            num_sellers=len(current_sellers),
            num_already_checkedin=len(checkedin_sellers),
            user=current_user,
        )

    logging.info("Someone without org right tried access the checkin list.")
    return redirect(url_for("session_handling.login"))


@checkin_routes.route("/org/checkin/<int:user_id>/", methods=["GET"])
def get_checkin(user_id):
    """Create the checking information."""

    current_user = User.query.get(session["user_id"])
    if current_user and current_user.organizer:
        checkin_user = db.session.get(User, user_id)
        articles_over = []
        articles_under = []

        provision = 0

        for article in filter(_filter_article_current, checkin_user.articles):
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
            "org/checkin/checkin.html",
            checkin_user=checkin_user,
            articles_under=articles_under,
            articles_over=articles_over,
            provision=provision,
            user=current_user,
        )

    logging.info("Someone tried to navigate the login page without being an org.")
    return redirect(url_for("session_handling.login"))


@checkin_routes.route("/org/checkin/done/<int:user_id>/", methods=["POST"])
def set_checkin(user_id):
    """Mark an seller as checked in."""
    current_user: User = User.query.get(session["user_id"])
    if current_user and current_user.organizer:
        user = db.session.get(User, user_id)
        user.checkin_done = True
        user.checkin_comment = request.form.get("comment", None)
        db.session.commit()

        logging.info(f"Checking for user {user_id} was closed.")

        return redirect(url_for("checkin_routes.return_checking_page"))

    logging.info("Someone without org right tried to do a checkin.")
    return redirect(url_for("session_handling.login"))


@checkin_routes.route("/org/checkin/<int:user_id>/<string:art_uuid>/remove", methods=["GET", "POST"])
def remove_article(user_id, art_uuid):
    """Permanently remove an article from the checkin screen."""
    current_user: User = User.query.get(session["user_id"])
    if current_user and current_user.organizer:
        if art_uuid is None:
            return abort(Response("Article UUID missing."))

        article = Article.query.get(art_uuid)
        
        db.session.delete(article)
        db.session.commit()

        logging.info(f"Article with UUID {art_uuid} was removed.")

        return redirect(url_for("checkin_routes.get_checkin", user_id=user_id))
    
    logging.error(
        f"User {current_user.id } tried to delete article {art_uuid} but is not allowed to."
    )
    return redirect(url_for("login"))
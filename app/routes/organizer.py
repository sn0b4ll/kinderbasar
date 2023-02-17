'''Serves pages linked to organizer functions.'''
# pylint: disable=no-member,logging-fstring-interpolation,import-error

import pdfkit #pylint: disable=import-error

from flask import Blueprint, Response
from flask import render_template, redirect, url_for
from flask import session

from models import db
from models import User

from helper import logging, _filter_article_current

organization_routes = Blueprint('organization_routes', __name__, template_folder='templates')

@organization_routes.route("/org/checkin/<int:user_id>/", methods=["GET"])
def get_checkin(user_id):
    '''Create the checking information.'''

    loggedin_user = User.query.get(session['user_id'])
    if loggedin_user.organizer:
        user = db.session.get(User, user_id)
        articles_over = []
        articles_under = []

        provision = 0

        for article in filter(_filter_article_current, user.articles):
            # Calculate provision
            if article.price < 5000:
                provision += article.price*0.05
            else:
                provision += 250


            # Depending on price, sort into under or over
            if article.price < 1000:
                articles_under.append(article)
            else:
                articles_over.append(article)

        return render_template(
            'checkin.html',
            user=user,
            articles_under=articles_under,
            articles_over=articles_over,
            provision=provision,
            org=True
        )

    logging.info("Someone tried to navigate the login page without being an org.")
    return redirect(url_for('session_handling.login'))

@organization_routes.route("/org/checkin/done/<int:user_id>/", methods=["POST"])
def set_checkin(user_id):
    '''Create the checking information.'''
    loggedin_user = User.query.get(session['user_id'])
    if loggedin_user.organizer:
        user = db.session.get(User, user_id)
        user.checkin_done = True
        db.session.commit()

        logging.info(f"Checking for user {user_id} was closed.")

        return redirect(url_for('organization_routes.get_sellers'))

    logging.info("Someone without org right tried to do a checkin.")
    return redirect(url_for('session_handling.login'))


@organization_routes.route("/sellers/", methods=["GET"])
def get_sellers():
    '''List all sellers with their sold / unsold product count.'''

    loggedin_user = User.query.get(session['user_id'])
    if loggedin_user.organizer:
        all_users = User.query.all()

        num_sellers = len(all_users)
        num_already_checkedin = 0

        seller_list = []
        for user in all_users:
            articles = list(filter(_filter_article_current, user.articles))
            articles_overall = len(articles)
            articles_sold = 0
            for article in articles:
                if article.sold is True:
                    articles_sold += 1

            if user.checkin_done:
                num_already_checkedin += 1

            seller_list.append(
                (
                    user,
                    articles_overall,
                    articles_sold,
                    user.checkin_done
                )
            )

        return render_template(
            'sellers.html',
            seller_list=seller_list,
            num_sellers=num_sellers,
            num_already_checkedin=num_already_checkedin,
            org=True
        )

    logging.info("Someone without org right tried access the sellers list.")
    return redirect(url_for('session_handling.login'))

@organization_routes.route("/clearing/<int:user_id>/", methods=["GET"])
def get_clearing(user_id):
    '''Get the final clearing document for a user after the basar ended.'''
    if ('organizer' in session) and (session['organizer'] is True):
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
            'clearing.html',
            user=user,
            articles_unsold=articles_unsold_abv10,
            sold_sum=sold_sum
        )

    logging.info("Someone without org right tried access the clearing for an seller.")
    return redirect(url_for('overview'))

@organization_routes.route("/clearing/printall", methods=["GET"])
def print_all_clearings():
    '''Create a pdf holding all clearings for all users.'''
    loggedin_user = User.query.get(session['user_id'])
    if loggedin_user.organizer:
        users = db.session.query(User).all()

        user_dict = {}

        for user in users:
            articles = user.articles

            articles_unsold_abv10 = []
            sold_sum = 0

            for article in filter(_filter_article_current, articles):
                if article.sold is True:
                    sold_sum += article.price
                elif article.price >= 1000:
                    articles_unsold_abv10.append(article)

            user_dict[user] = {"articles" : articles_unsold_abv10, "sold_sum" : sold_sum}

        html = render_template(
            'clearing_all.html',
            users=users,
            user_dict=user_dict
        )

        options = {
            'page-height': '297mm',
            'page-width': '210mm',
        }

        return Response(pdfkit.from_string(html, options=options),
                       mimetype="application/pdf",
                       headers={"Content-Disposition":
                                    "attachment;filename=clearing.pdf"})

    logging.info("Someone without the right tried access the clearing for an seller.")
    return redirect(url_for('session_handling.login'))

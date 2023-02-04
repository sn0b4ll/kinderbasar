'''Serves pages linked to organizer functions.'''
# pylint: disable=no-member,logging-fstring-interpolation

import logging

from configparser import ConfigParser

from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import session

from models import db
from models import User

# Init config parser
config = ConfigParser()
config.read('./conf/env.conf') # TODO(Do only once -> own module)

# Init logging
logging.basicConfig( # TODO(Do only once -> own module)
    filename='./logs/kinderbasar.log', 
    format='%(asctime)s:%(levelname)s:%(message)s', 
    level=logging.DEBUG
)

organization_routes = Blueprint('organization_routes', __name__, template_folder='templates')

@organization_routes.route("/org/checkin/<int:user_id>/", methods=["GET"])
def get_checkin(user_id):
    '''Create the checking information.'''
    if ('organizer' in session) and (session['organizer'] is True):
        user = db.session.get(User, user_id)
        articles_over = []
        articles_under = []

        provision = 0

        for article in user.articles:
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

@organization_routes.route("/org/checkin/done/<int:user_id>/", methods=["POST"])
def set_checkin(user_id):
    '''Create the checking information.'''
    if ('organizer' in session) and (session['organizer'] is True):
        user = db.session.get(User, user_id)
        user.checkin_done = True
        db.session.commit()

        return redirect(url_for('organization_routes.get_sellers'))



@organization_routes.route("/sellers/", methods=["GET"])
def get_sellers():
    '''List all sellers with their sold / unsold product count.'''
    if ('organizer' in session) and (session['organizer'] is True):
        all_users = User.query.all()
        
        num_sellers = len(all_users)
        num_already_checkedin = 0
        
        seller_list = []
        for user in all_users:
            articles = user.articles
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

    return redirect(url_for('overview'))

@organization_routes.route("/clearing/<int:user_id>/", methods=["GET"])
def get_clearing(user_id):
    '''Get the final clearing document for a user after the basar ended.'''
    if ('organizer' in session) and (session['organizer'] is True):
        user = db.session.get(User, user_id)
        articles = user.articles

        articles_sold = []
        articles_unsold = []

        sold_sum = 0
        for article in articles:
            if article.sold is True:
                sold_sum += article.price
                articles_sold.append(article)
            else:
                articles_unsold.append(article)

        return render_template(
            'clearing.html',
            user=user,
            articles_sold=articles_sold,
            articles_unsold=articles_unsold,
            sold_sum=sold_sum
        )

    return redirect(url_for('overview'))
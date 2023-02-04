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

@organization_routes.route("/sellers/", methods=["GET"])
def get_sellers():
    '''List all sellers with their sold / unsold product count. '''
    if ('organizer' in session) and (session['organizer'] == True):
        all_users = User.query.all()
        seller_list = []
        for user in all_users:
            articles = user.articles
            articles_overall = len(articles)
            articles_sold = 0
            for article in articles:
                if article.sold == True:
                    articles_sold += 1

            seller_list.append(
                (
                    user,
                    articles_overall,
                    articles_sold
                )
            )

        return render_template(
            'sellers.html',
            seller_list=seller_list,
            org=True
        )

    return redirect(url_for('overview'))

@organization_routes.route("/clearing/<int:user_id>/", methods=["GET"])
def get_clearing(user_id):
    '''Get the final clearing document for a user after the basar ended.'''
    if ('organizer' in session) and (session['organizer'] == True):
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
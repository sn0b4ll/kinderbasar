"""This is the main module holding all the routes and app logic."""

import uuid
import math
import logging

from configparser import ConfigParser

import pdfkit

from flask import Flask, Response
from flask import render_template
from flask import redirect, url_for
from flask import session

from argon2 import PasswordHasher

from flask_qrcode import QRcode

from models import db

from routes.register import register_process
from routes.session import session_handling
from routes.article import article_handling
from routes.card import card_handling

# Init config parser
config = ConfigParser()
config.read('./conf/env.conf')

app = Flask(__name__)
app.secret_key = config.get('APP', 'secret_key')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../db/test.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://kinderbasar:passpass@db/kinderbasar'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db.init_app(app)

app.register_blueprint(register_process)
app.register_blueprint(session_handling)
app.register_blueprint(article_handling)
app.register_blueprint(card_handling)

from models import  Article, User, Card

from tests.data import create_test_data

# Init logging
logging.basicConfig(
    filename='./logs/kinderbasar.log', 
    format='%(asctime)s:%(levelname)s:%(message)s', 
    level=logging.DEBUG
)

# Init password hasher
# https://pypi.org/project/argon2-cffi/
ph = PasswordHasher()

# Load QR Module
QRcode(app)

# Routes
@app.route("/")
def home():
    """ Returns the default page - either overview or login, based on the status of the session."""
    if 'user_id' in session:
        if User.query.get(session['user_id']) is not None:
            return redirect(url_for('overview'))
        else:
            return redirect(url_for('login'))    
    else:
        return redirect(url_for('login'))

@app.route("/overview", methods=["GET"])
def overview():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if ('organizer' in session) and (session['organizer'] == True):
            articles = Article.query.all()
            org = True
        else:
            articles = user.articles
            org = False

        return render_template(
                'overview.html',
                user=user,
                articles=articles,
                org=org
            )
    else:
        return redirect(url_for('login'))


@app.route("/overview/qr", methods=["GET"])
def overview_qr():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        
        html = render_template(
                'overview_qr.html',
                articles=user.articles,
                url_template=f"{config['APP']['URL']}/article/"
            )

        options = {
            'page-height': '297mm', 
            'page-width': '210mm',
        }

        return Response(pdfkit.from_string(html, options=options),
                       mimetype="application/pdf",
                       headers={"Content-Disposition":
                                    "attachment;filename=kinderbasar.pdf"})
    else:
        return redirect(url_for('login'))

@app.route("/shopping_basket/add", methods=["GET"])
def add_shopping_basket():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

        if user.registration_done:
            return "Registration already done.", 403

        shopping_basket = Article()
        shopping_basket.name = "Einkaufskorb"
        shopping_basket.uuid = str(uuid.uuid4())
        shopping_basket.price = 0
        shopping_basket.sold = True
        shopping_basket.seller = user

        db.session.add(shopping_basket)
        db.session.commit()

        logging.info(f"The shopping basket {shopping_basket.uuid} was created.")

        return redirect(url_for('overview'))
    else:
        return redirect(url_for('login'))

@app.route("/registration_sheet/", methods=["GET"])
def get_registration_sheet():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

        articles = user.articles

        article_sum = 0
        for article in articles:
            article_sum += article.price

        registration_fee = article_sum * 0.05

        return render_template(
            'registration_sheet.html',
            user=user,
            articles=articles,
            article_sum=article_sum,
            registration_fee=registration_fee
        )
    else:
        return redirect(url_for('overview'))

@app.route("/sellers/", methods=["GET"])
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
    else:
        return redirect(url_for('overview'))

@app.route("/clearing/<int:id>/", methods=["GET"])
def get_clearing(id):
    if ('organizer' in session) and (session['organizer'] == True):
        user = User.query.get(id)
        articles = user.articles

        articles_sold = []
        articles_unsold = []

        sold_sum = 0
        for article in articles:
            if article.sold == True:
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
    else:
        return redirect(url_for('overview'))

@app.route("/user/registration_done", methods=["POST"])
def registration_done():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        user.registration_done = True
        db.session.commit()
        return f"Registration done set for user { user.id }", 200
    else:
        return redirect(url_for('login'))


def as_euro(price):
    '''Display an int as euro.'''
    if type(price) == int:
        price = str(price)
    elif type(price) == float:
        price = str(math.ceil(price/10)*10)

    euro = price[:-2]
    if euro == "": euro = "0"
    cent = price[-2:]
    price = f'{euro},{cent}€'
    return price

def to_german(orig):
    '''Translate default terms to german.'''
    if orig == "True" or orig is True:
        return "Ja"
    elif orig == "False" or orig is False:
        return "Nein"
    elif orig is None:
        return ""
    else:
        return orig

if __name__ == '__main__':
    app.app_context().push()

    # Create the database
    db.create_all()

    # Remove before production
    create_test_data()

    app.jinja_env.filters['as_euro'] = as_euro
    app.jinja_env.filters['to_german'] = to_german
    app.run(debug=config.getboolean('APP', 'DEBUG'), host='0.0.0.0')

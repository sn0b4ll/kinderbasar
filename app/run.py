"""This is the main module holding all the routes and app logic."""

from http.client import OK
import uuid
import math
import logging
import pdfkit

from configparser import ConfigParser
from random import random
from time import sleep

from flask import Flask
from flask import abort
from flask import render_template
from flask import request
from flask import redirect, url_for, Response
from flask import session

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from flask_qrcode import QRcode

from models import db

from routes.register import register_process

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

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        sleep(random()) # Let's slow bots down..
        email = request.form['username']
        password = request.form['password']

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user is None:
            # and if not, return to the login page
            return render_template(
                'login.html',
                title="Login"
            )

        pass_hash = user.password
        salt = user.salt

        try:
            ph.verify(pass_hash, password+salt)
        except VerifyMismatchError:
            # Verify failed
            logging.warning(f"Failed login attemp for user {user.email}.")
            return render_template(
                'login.html',
                title="Login"
            )
        except:
            # Something else went wrong, but better be sure not to skip this check
            return render_template(
                'login.html',
                title="Login"
            )

        if not user.activated: # Eventuell Warnung anzeigen
            return render_template(
                'login.html',
                title="Login"
            )

        # All checks passed :)
        session['user_id'] = user.id
        session['organizer'] = user.organizer
        logging.info(f"User {user.id}/{user.email} logged in successfully.")
        return redirect(url_for('overview'))
    else:
        return render_template(
            'login.html',
            title="Login"
        )

@app.route("/logout")
def logout():
    if 'user_id' in session:
        logging.info(f"User {session['user_id']} logged out.")
        session.pop('user_id')
        session.pop('organizer')
    return redirect(url_for('login'))

@app.route("/article/add", methods=["GET", "POST"])
def add_article():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.registration_done:
            return "Registration already finished.", 403


        if request.method == 'GET':
            return render_template(
                'add_article.html',
                title="Add an article"
            )
        else:
            name = request.form['name']
            price = request.form['price']
            try:
                price = price.replace(',', '')
                price = price.replace('€', '')
                price = price.replace('.', '')
                price = int(price)
            except:
                return "Bitte beachten Sie die Vorgaben zur Preiseingabe. Sie erreichen die vorherige Seite über den Zurück-Button Ihres Browsers."

            clothing_size = request.form['clothing_size']

            article = Article()
            article.uuid = str(uuid.uuid4())
            article.name = name
            article.seller = User.query.get(session['user_id'])
            article.clothing_size = clothing_size
            article.price = price
            article.sold = False
        
            db.session.add(article)
            db.session.commit()

            logging.info(f"Article {article.uuid}/{article.name} was created.")

            url = f"{config['APP']['URL']}/article/{article.uuid}"
            
            return redirect(url_for('overview'))
    else:
       return redirect(url_for('login'))

@app.route("/article/<string:uuid>", methods=["GET"])
def article_view(uuid):
    '''Return the view for a single article.'''
    if uuid is None:
        logging.debug(f"There was a try to access an not existing article {uuid}.")
        return abort(Response('Article UUID missing.'))
    if ('organizer' in session) and (session['organizer'] == True):
        org = True
    else:
        org = False

    article = Article.query.filter_by(uuid=uuid).first()

    return render_template(
        'article.html',
        article=article,
        org=org
    )

@app.route("/article/<string:uuid>/remove", methods=["GET", "POST"])
def remove_article(uuid):
    if 'user_id' in session:
        if uuid is None:
            return abort(Response('Article UUID missing.'))

        user = User.query.get(session['user_id'])
        article = Article.query.get(uuid)

        if (not article in user.articles) or user.registration_done or article.sold:
            return "Not allowed to delete article.", 403

        db.session.delete(article)
        db.session.commit()

        logging.info(f"Article with UUID {uuid} was removed.")

        return redirect(url_for('overview'))

'''
Disabled, since it is no longer needed.

@app.route("/article/<string:uuid>/qr", methods=["get"])
def print_qr(uuid):
    url = f"{config['APP']['URL']}/article/{uuid}"

    article = Article.query.filter_by(uuid=uuid).first()
    if article is None:
            abort(Response('UUID for article is not existing.'))
    return render_template(
        'qr_code.html',
        url=url, 
        article=article
    )
'''

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

@app.route("/card/<string:uuid>/", methods=["GET"])
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

@app.route("/card/<string:card_uuid>/add/<string:article_uuid>/", methods=["POST"])
def add_article_to_card(card_uuid, article_uuid):
    if ('organizer' in session) and (session['organizer'] == True) :
        if card_uuid == "active":
            uuid = _get_card_uuid_for_user()

        card = Card.query.get(uuid)

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

@app.route("/card/<string:uuid>/close/", methods=["POST"])
def close_card(uuid):
    if ('organizer' in session) and (session['organizer'] == True) :
        if uuid == "active":
            uuid = _get_card_uuid_for_user()
        
        card = Card.query.get(uuid)
        
        if card is None:
            return "Card not found."

        if card.user_id != session['user_id']:
            return "Wrong Session!"

        card.active = False

        for article in card.articles:
            article.sold = True

        db.session.commit()

        logging.info(f"The card {uuid} was closed.")

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
    if (type(price) == int):
        price = str(price)
    elif (type(price) == float):
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

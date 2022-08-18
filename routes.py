import uuid
import json
import math

from argon2 import PasswordHasher

from configparser import ConfigParser

from flask import Flask
from flask import abort
from flask import render_template
from flask import request
from flask import redirect, url_for, Response
from flask import session
from flask_sqlalchemy import SQLAlchemy

from random import random
from time import sleep

from werkzeug.exceptions import BadRequestKeyError

from flask_qrcode import QRcode

from models import db

app = Flask(__name__)
app.secret_key = 'set_me_to_something_random_please'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db.init_app(app)

from models import  Article, User, Card

# Init config parser
config = ConfigParser()
config.read('env.conf')


# Init password hasher
# https://pypi.org/project/argon2-cffi/
ph = PasswordHasher()

# Load QR Module
QRcode(app)

# Routes
@app.route("/")
def home():
    if 'user_id' in session:
        return redirect(url_for('overview'))
    else:
        return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        sleep(random()) # Let's slow bots down..
        id = request.form['username']
        password = request.form['password']

        user = User.query.get(id)
        hash = user.password
        salt = user.salt
        if (user is not None) and \
            (ph.verify(hash, password+salt)) and \
                (user.activated):
            session['user_id'] = user.id
            session['organizer'] = user.organizer
            return redirect(url_for('overview'))
        return "User-ID oder Passwort falsch oder E-Mail wurde nicht bestätigt."

    else:
        return render_template(
            'login.html',
            title="Login"
        )

@app.route("/register", methods=["POST"])
def register():
    sleep(random())
    email = request.form['email']
    existing_user = False
    for user in User.query.all():
        if user.email == email:
            existing_user = True
            tmp_user = user
            break

    if existing_user:
        # If the user exists but the E-Mail is not actived yet, it should be allowed to overwrite the params
        # of the existing User
        if tmp_user.activated:
            return "User already registered" # TODO (Prevent enum)
        else:
            user = tmp_user
    else:
        user= User()

    salt = str(uuid.uuid4())
    hash = ph.hash(request.form['password'] + salt)
    activation_code = str(uuid.uuid4())
    user.password = hash
    user.salt = salt
    user.email = email
    user.activation_code = activation_code
    user.activated = False
    user.organizer = False

    db.session.add(user)
    db.session.commit()

    # Import smtplib for the actual sending function
    import smtplib

    from email.message import EmailMessage

    msg = EmailMessage()
    msg.set_content(f'''Vielen Dank für Ihre Registrierung.
    
Bitte aktivieren Sie Ihren Account hier: {config['APP']['URL']}/activate/{user.id}/{activation_code}

Vielen Dank & viel Erfolg wünscht Ihnen
Ihr Kinderbasar Elsendorf Team
    ''')



    msg['From'] = "info@kinderbasar-elsendorf.de"
    msg['To'] = email
    msg['Subject'] = f'Registrierung'

    print(config['EMAIL']['server'])

    s = smtplib.SMTP_SSL(config['EMAIL']['server'], 465) # TODO(Port)
    s.login(config['EMAIL']['username'], config['EMAIL']['password'])
    s.send_message(msg)
    s.quit()

    message = "Erfolg!"

    return render_template(
        'notes.html',
        title="Danke!",
        message=message
    )

@app.route("/activate/<int:id>/<string:uuid>")
def activate(id, uuid):
    sleep(random()) # Let's slow bots down..
    user = User.query.get(id)
    if user is not None:
        if user.activation_code == uuid:
            user.activated = True
            db.session.commit()
            return "Die Aktivierung war erfolgreich - Sie können sich jetzt mit ihrer User-ID & ihrem Passwort anmelden"
    
    return "User-ID oder Aktivierungs-Code falsch"

@app.route("/logout")
def logout():
    if 'user_id' in session:
        session.pop('user_id')
        session.pop('organizer')
    return redirect(url_for('login'))

@app.route("/article/add", methods=["GET", "POST"])
def add_article():
    if 'user_id' in session:
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
            article.seller = session['user_id']
            article.clothing_size = clothing_size
            article.price = price
            article.sold = False
        
            db.session.add(article)
            db.session.commit()

            url = f"{config['APP']['URL']}/article/{article.uuid}"
            
            return redirect(url_for('overview'))
    else:
       return redirect(url_for('login'))

@app.route("/article/<string:uuid>", methods=["GET"])
def article_view(uuid):
        if uuid is None:
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

        if article.seller != user.id:
            return "Not allowed to delete article.", 403

        db.session.delete(article)
        db.session.commit()

        return redirect(url_for('overview'))

@app.route("/article/<string:uuid>/qr", methods=["get"])
def print_qr(uuid):
    url = f"{config['APP']['URL']}/article/{article.uuid}"

    article = Article.query.filter_by(uuid=uuid).first()
    if article is None:
            abort(Response('UUID for article is not existing.'))
    return render_template(
        'qr_code.html',
        url=url, 
        article=article
    )

@app.route("/overview", methods=["GET"])
def overview():
    if 'user_id' in session:
        if ('organizer' in session) and (session['organizer'] == True):
            articles = Article.query.all()
            org = True
        else:
            articles = Article.query.filter_by(seller=session['user_id'])
            org = False

        return render_template(
                'overview.html',
                articles=articles,
                org=org
            )
    else:
        return redirect(url_for('login'))

@app.route("/overview/qr", methods=["GET"])
def overview_qr():
    # pass all articles for currently logged in user to template
    if 'user_id' in session:
        articles = Article.query.filter_by(seller=session['user_id'])

        return render_template(
                'overview_qr.html',
                articles=articles,
                url_template=f"{config['APP']['URL']}/article/"
            )
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
    if ('organizer' in session) and (session['organizer'] == True) :
        if uuid == "active":
            uuid = _get_card_uuid_for_user()

        card = Card.query.get(uuid)
        
        if card is None:
            return "Card not found."

        print(type(card.user_id))
        print(session['user_id'])
        if card.user_id != session['user_id']:
            return "Wrong Session!"

        price_overall = 0
        for article in card.articles:
            price_overall += int(article.price)
        
        return render_template(
                'card.html',
                card=card,
                price_overall=price_overall
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
        
        return render_template(
                'card.html',
                card=card,
                price_overall=price_overall
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

        price_overall = 0
        for article in card.articles:
            price_overall += int(article.price)
        
        return render_template(
                'card.html',
                card=card,
                price_overall=price_overall,
                org=True
            )
    else:
        return redirect(url_for('login'))

@app.route("/add_shopping_basket/", methods=["GET"])
def add_shopping_basket():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        shopping_basket = Article()
        shopping_basket.name = "Einkaufskorb"
        shopping_basket.uuid = str(uuid.uuid4())
        shopping_basket.price = 0
        shopping_basket.sold = True
        shopping_basket.seller = user.id

        db.session.add(shopping_basket)
        db.session.commit()

        return redirect(url_for('overview'))
    else:
        return redirect(url_for('login'))



@app.route("/registration_sheet/", methods=["GET"])
def get_registration_sheet():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

        articles = Article.query.filter_by(seller=session['user_id'])

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
    

if __name__ == '__main__':
    app.app_context().push()
    db.create_all()

    
    # Test-Data
    print("Creating test data")
    user = User()
    user.salt = str(uuid.uuid4())
    user.password = ph.hash("abcd"+user.salt)
    user.email = "testuser1@user.de"
    user.name = "testuser1"
    user.organizer = False
    user.activated = True
    db.session.add(user)

    user2 = User()
    user2.salt = str(uuid.uuid4())
    user2.password = ph.hash("abcd"+user.salt)
    user2.email = "testuser2@user.de"
    user2.name = "testuser2"
    user2.organizer = True
    user2.activated = True
    db.session.add(user2)

    db.session.commit()

    article = Article()
    article.uuid = str(uuid.uuid4())
    article.name = "Testname"
    article.seller = user.id
    article.clothing_size = ""
    article.price = 1337
    article.sold = False
    db.session.add(article)

    article2 = Article()
    article2.uuid = str(uuid.uuid4())
    article2.name = "Testname2"
    article2.seller = user.id
    article2.clothing_size = "42"
    article2.price = 2456
    article2.sold = False
    db.session.add(article2)

    article3 = Article()
    article3.uuid = str(uuid.uuid4())
    article3.name = "Testname3"
    article3.seller = user.id
    article3.clothing_size = "42"
    article3.price = 2456
    article3.sold = False
    db.session.add(article3)

    card = Card()
    card.uuid = str(uuid.uuid4())
    card.articles = [article, article2]
    card.active = True
    db.session.add(card)

    user2.cards = [card]
    

    db.session.commit()
    
    
    app.jinja_env.filters['as_euro'] = as_euro
    app.run(debug=True, host='0.0.0.0')
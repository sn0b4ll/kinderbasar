import uuid
import json

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
        if (user is not None) and \
            (ph.verify(hash, password)) and \
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
    email = request.form['email']
    hash = ph.hash(request.form['password'])
    activation_code = str(uuid.uuid4())

    # TODO(Check ob adresse schon vorhanden)
    # TODO(Salting)
    user= User()
    user.password = hash
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

            article = Article()
            article.uuid = str(uuid.uuid4())
            article.name = name
            article.seller = session['user_id']
            article.price = price
            article.sold = False
        
            db.session.add(article)
            db.session.commit()

            url = "http://192.168.1.36:5000/article/" + article.uuid
            
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

@app.route("/article/<string:uuid>/qr", methods=["get"])
def print_qr(uuid):
    url = "http://192.168.1.36:5000/article/" + uuid

    article = Article.query.filter_by(uuid=uuid).first()
    if article is None:
            abort(Response('UUID for article is not existing.'))
    return render_template(
        'qr_code.html',
        url=url, 
        article=article
    )


@app.route("/article/<string:uuid>/sold", methods=["POST"])
def article_sold(uuid):
    if ('organizer' in session) and (session['organizer'] == True):
        org = True
        article = Article.query.filter_by(uuid=uuid).first()
        article.sold = True
        article.price = request.form['price']

        db.session.commit()

        return render_template(
            'article.html',
            article=article,
            org=org
        )
    else:
        abort(403) 

@app.route("/overview", methods=["GET"])
def overview():
    if 'user_id' in session:
        if ('organizer' in session) and (session['organizer'] == True):
            articles = Article.query.all()
        else:
            articles = Article.query.filter_by(seller=session['user_id'])

        return render_template(
                'overview.html',
                articles=articles
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
                url_template="http://192.168.1.36:5000/article/" # TODO(Config file)
            )
    else:
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.app_context().push()
    db.create_all()

    '''
    # Test-Data
    print("Creating test data")
    user = User()
    user.password = ph.hash("abcd")
    user.email = "testuser1@user.de"
    user.name = "testuser1"
    user.organizer = False
    user.activated = True
    db.session.add(user)

    user2 = User()
    user2.password = ph.hash("abcd")
    user2.email = "testuser2@user.de"
    user2.name = "testuser2"
    user2.organizer = True
    user2.activated = True
    db.session.add(user2)

    article = Article()
    article.uuid = str(uuid.uuid4())
    article.name = "Testname"
    article.seller = user.id
    article.price = "13.37"
    article.sold = False
    db.session.add(article)

    article2 = Article()
    article2.uuid = str(uuid.uuid4())
    article2.name = "Testname2"
    article2.seller = user.id
    article2.price = "13.37"
    article2.sold = False
    db.session.add(article2)

    card = Card()
    card.uuid = str(uuid.uuid4())
    card.articles = [article, article2]
    db.session.add(card)

    user2.cards = [card]
    

    db.session.commit()
    '''

    app.run(debug=True, host='0.0.0.0')
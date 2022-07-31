import uuid
import json

from flask import Flask
from flask import abort
from flask import render_template
from flask import request
from flask import redirect, url_for, Response
from flask import session
from flask_sqlalchemy import SQLAlchemy

from werkzeug.exceptions import BadRequestKeyError

from flask_qrcode import QRcode

app = Flask(__name__)
app.secret_key = 'set_me_to_something_random_please'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

'''
---- Database ----
'''

db = SQLAlchemy(app)
QRcode(app)

class Article(db.Model):
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    seller = db.Column(db.Integer)
    price = db.Column(db.String)
    sold = db.Column(db.Boolean)

    def __repr__(self):
        return f"<Article(uuid='{self.uuid}', name='{self.name}', seller='{self.seller}', price='{self.price}, sold='{self.sold}'"

class User(db.Model):
    uuid = db.Column(db.String, primary_key=True)
    secret = db.Column(db.String)
    organizer = db.Column(db.Boolean)

db.create_all()

user = User()
user.uuid = str(uuid.uuid4())
user.secret = "abcd"
user.organizer = False
db.session.add(user)

# Test-Data
article = Article()
article.uuid = str(uuid.uuid4())
article.name = "Testname"
article.seller = user.uuid
article.price = "13.37"
article.sold = False
db.session.add(article)

db.session.commit()

'''
---- Routes ----
'''
@app.route("/")
def home():
    if 'seller_uuid' in session:
        return redirect(url_for('overview'))
    else:
        return redirect(url_for('login'))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        uuid = request.form['username']
        secret = request.form['password']

        user = User.query.get(uuid)
        if (user is not None) and (user.secret == secret):
            session['seller_uuid'] = user.uuid
            session['organizer'] = user.organizer
            return redirect(url_for('overview'))
        return "Nope"

    else:
        return render_template(
            'login.html',
            title="Login"
        )

@app.route("/logout")
def logout():
    if 'seller_uuid' in session:
        session.pop('seller_uuid')
        session.pop('organizer')
    return redirect(url_for('login'))

@app.route("/article/add", methods=["GET", "POST"])
def add_article():
    if 'seller_uuid' in session:
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
            article.seller = session['seller_uuid']
            article.price = price
            article.sold = False
        
            db.session.add(article)
            db.session.commit()

            url = "http://192.168.1.36:5000/article/" + article.uuid
            
            return render_template(
                'qr_code.html',
                url=url, 
                article=article
            )
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
    if 'seller_uuid' in session:
        if ('organizer' in session) and (session['organizer'] == True):
            articles = Article.query.all()
        else:
            articles = Article.query.filter_by(seller=session['seller_uuid'])

        return render_template(
                'overview.html',
                articles=articles
            )
    else:
        return redirect(url_for('login'))

@app.route("/overview/qr", methods=["GET"])
def overview_qr():
    # pass all articles for currently logged in user to template
    if 'seller_uuid' in session:
        articles = Article.query.filter_by(seller=session['seller_uuid'])

        return render_template(
                'overview_qr.html',
                articles=articles,
                url_template="http://192.168.1.36/article/" # TODO(Config file)
            )
    else:
        return redirect(url_for('login'))
import uuid
import json

from flask import Flask
from flask import render_template
from flask import request
from flask import redirect, url_for
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
    return render_template(
        'home.html',
        title="Jinja Demo Site",
        description="Description"
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        uuid = request.form['username']
        secret = request.form['password']

        
        user = User.query.get(uuid)
        if (user is not None) and (user.secret == secret):
            session['seller_uuid'] = user.uuid
            session['organizer'] = user.organizer
            return redirect(url_for('seller'))
        return "Nope"

    else:
        return render_template(
            'login.html',
            title="Login"
        )

@app.route("/logout")
def logout():
    session.pop('seller_uuid')
    session.pop('organizer')
    return redirect(url_for('login'))

@app.route("/add_article")
def add_article():
    if 'seller_uuid' in session:
        return render_template(
            'add_article.html',
            title="Add an article"
        )
    else:
       return redirect(url_for('login'))

@app.route("/article", methods=["GET", "POST"])
def article():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']

        print(name, price)

        article = Article()
        article.uuid = str(uuid.uuid4())
        article.name = name
        article.seller = session['seller_uuid']
        article.price = price
        article.sold = False
    
        db.session.add(article)
        db.session.commit()

        url = "http://192.168.1.36:5000/article?uuid=" + article.uuid
        #return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
        return render_template(
            'qr_code.html',
            url=url, 
            article=article
        )
    else:
        args = request.args
        article = Article.query.filter_by(uuid=args['uuid']).first()
        if ('organizer' in session) and (session['organizer'] == True):
            org = True
        else:
            org = False
        print("Org:" + str(org))
        return render_template(
            'article.html',
            article=article,
            org=org
        )

@app.route("/article/<string:uuid>/sold", methods=["POST"])
def article_sold(uuid):
    article = Article.query.filter_by(uuid=uuid).first()
    article.sold = True
    article.price = request.form['price']

    db.session.commit()

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

@app.route("/seller", methods=["GET"])
def seller():
    articles = Article.query.filter_by(seller=session['seller_uuid'])

    return render_template(
            'seller.html',
            articles=articles
        )

db.session.close()

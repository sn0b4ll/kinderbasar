import uuid
import json

from flask import Flask
from flask import render_template
from flask import request
from flask_sqlalchemy import SQLAlchemy

from flask_qrcode import QRcode

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

db = SQLAlchemy(app)
QRcode(app)

class Article(db.Model):
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    seller = db.Column(db.Integer)
    price = db.Column(db.String)
    sold = db.Column(db.Boolean) # Was boolean, not working on development environment at least..

    def __repr__(self):
        return f"<Article(uuid='{self.uuid}', name='{self.name}', seller='{self.seller}', price='{self.price}, sold='{self.sold}'"

db.create_all()

@app.route("/")
def home():
    return render_template(
        'home.html',
        title="Jinja Demo Site",
        description="Description"
    )

@app.route("/add_article")
def add_article():
    return render_template(
        'add_article.html',
        title="Add an article"
    )

@app.route("/article", methods=["GET", "POST"])
def article():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']

        print(name, price)

        article = Article()
        article.uuid = str(uuid.uuid4())
        article.name = name
        article.seller = "Seller"
        article.price = price
        article.sold = False
    
        db.session.add(article)
        db.session.commit()

        url = "http://192.168.1.36:5000/article?uuid=" + article.uuid
        #return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
        return render_template(
            'qr_code.html',
            url=url
        )
    else:
        args = request.args
        article = Article.query.filter_by(uuid=args['uuid']).first()
        return render_template(
            'article.html',
            article=article
        )

@app.route("/article/<string:uuid>/sold", methods=["POST"])
def article_sold(uuid):
    article = Article.query.filter_by(uuid=uuid).first()
    article.sold = True
    article.price = request.form['price']

    db.session.commit()

    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 

print("test")

article = Article()
article.uuid = str(uuid.uuid4())
article.name = "Testname"
article.seller = "Seller"
article.price = "13.37"
article.sold = False

db.session.add(article)
db.session.commit()

for article in db.session.query(Article).all():
    print(article)
    if article.sold:
        print("Was sold!")

db.session.close()

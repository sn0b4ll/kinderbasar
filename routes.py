import uuid
import json

from flask import Flask
from flask import render_template
from flask import request
from model import session, Article

from flask_qrcode import QRcode

app = Flask(__name__)

QRcode(app)

@app.route("/")
def home():
    return render_template(
        'home.html',
        title="Jinja Demo Site",
        description="Description"
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
        article.sold = "False"
    
        session.add(article)
        session.commit()
        return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
    else:
        return "Article Backend"


print("test")

article = Article()
article.uuid = str(uuid.uuid4())
article.name = "Testname"
article.seller = "Seller"
article.price = "13.37"
article.sold = "False"

session.add(article)
session.commit()

for article in session.query(Article).all():
    print(article)
    if article.sold == "True":
        print("Was sold!")

session.close()

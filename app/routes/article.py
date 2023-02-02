'''Serves pages linked to the article handling.'''
# pylint: disable=no-member,logging-fstring-interpolation

import uuid
import logging

from configparser import ConfigParser

from flask import Blueprint, Response
from flask import render_template, redirect, url_for, abort
from flask import request, session

from models import db
from models import Article, User

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
ph = PasswordHasher()

# Init config parser
config = ConfigParser()
config.read('./conf/env.conf') # TODO(Do only once -> own module)

# Init logging
logging.basicConfig( # TODO(Do only once -> own module)
    filename='./logs/kinderbasar.log', 
    format='%(asctime)s:%(levelname)s:%(message)s', 
    level=logging.DEBUG
)

article_handling = Blueprint('article_handling', __name__, template_folder='templates')

@article_handling.route("/article/add", methods=["GET", "POST"])
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

@article_handling.route("/article/<string:uuid>", methods=["GET"])
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

@article_handling.route("/article/<string:uuid>/remove", methods=["GET", "POST"])
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
'''Serves pages linked to the article handling.'''
# pylint: disable=no-member,logging-fstring-interpolation

import uuid

from flask import Blueprint, Response
from flask import render_template, redirect, url_for, abort
from flask import request, session

from models import db
from models import Article, User, Shoppingbasket

from helper import logging, config, ph

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
            article.current = True
            article.price = price
            article.sold = False
        
            db.session.add(article)
            db.session.commit()

            logging.info(f"Article {article.uuid}/{article.name} was created.")

            url = f"{config['APP']['URL']}/article/{article.uuid}"
            
            return redirect(url_for('overview'))
    else:
       return redirect(url_for('session_handling.login'))

@article_handling.route("/article/<string:uuid>", methods=["GET"])
def article_view(uuid):
    '''Return the view for a single article.'''
    if uuid is None:
        logging.debug(f"There was a try to access an not existing article {uuid}.")
        return abort(Response('Article UUID missing.'))
    try:
        user = User.query.get(session['user_id']) # TODO(Allow viewing of articles without login.)
    except KeyError:
        # Anonymous user
        user = None

    article = Article.query.filter_by(uuid=uuid).first()

    return render_template(
        'article.html',
        article=article,
        user=user
    )

@article_handling.route("/article/<string:article_uuid>/reactivate", methods=["GET", "POST"])
def reactivate_article(article_uuid):
    if 'user_id' in session:
        if article_uuid is None:
            return abort(Response('Article UUID missing.'))

        user = User.query.get(session['user_id'])
        article = Article.query.get(article_uuid)

        if article in user.articles:
            article.current = True
        else:
            return abort(Response('Article not linked to user.'))

        db.session.commit()

        return redirect(url_for('overview'))

    return abort(Response('Please login to use this functionality.'))


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

@article_handling.route("/shoppingbasket/add", methods=["GET"])
def add_shopping_basket():
    '''Add a shoping basket as an article.'''
    if 'user_id' in session:
        user = User.query.get(session['user_id'])

        if user.registration_done:
            return "Registration already done.", 403

        shopping_basket = Shoppingbasket()
        shopping_basket.owner = user

        db.session.add(shopping_basket)
        db.session.commit()

        logging.info(f"The shopping basket {shopping_basket.id} was created.")

        return redirect(url_for('overview'))
    else:
        return redirect(url_for('session_handling.login'))

@article_handling.route("/shoppingbasket/<string:basket_id>/remove", methods=["POST"])
def remove_basket(basket_id):
    if 'user_id' in session:
        if basket_id is None:
            return abort(Response('Basket ID missing.'))

        user = db.session.get(User, session['user_id'])
        shoppingbasket = db.session.get(Shoppingbasket, basket_id)

        if (not shoppingbasket in user.shoppingbaskets) or user.registration_done:
            return "Not allowed to delete basket.", 403

        db.session.delete(shoppingbasket)
        db.session.commit()

        logging.info(f"Basket with ID {basket_id} was removed.")

        return redirect(url_for('overview'))
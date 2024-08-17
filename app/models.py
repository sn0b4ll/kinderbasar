"""This file holds the DB-Model for the application."""
# pylint: disable=no-member,too-few-public-methods

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

ARTICLE_NAME_SIZE = 25
ARTICLE_COMMENT_SIZE = 25
CHECKIN_COMMENT_SIZE = 200

class Article(db.Model):
    """Article (everything which can be bought)."""

    uuid = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(ARTICLE_NAME_SIZE))
    price = db.Column(db.Integer)
    sold = db.Column(db.Boolean)
    comment = db.Column(db.String(ARTICLE_COMMENT_SIZE))
    current = db.Column(db.Boolean)  # Is the article in the current bazar run
    reactivated = db.Column(db.Boolean)
    last_current = db.Column(db.DateTime)
    cart_uuid = db.Column(db.String(36), db.ForeignKey('cart.uuid'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model):
    """Class for holding sellers and organizers."""

    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(100))
    salt = db.Column(db.String(36))
    email = db.Column(db.String(50))
    activation_code = db.Column(db.String(36))
    activated = db.Column(db.Boolean)
    organizer = db.Column(db.Boolean)
    checkin_done = db.Column(db.Boolean)
    checkin_comment = db.Column(db.String(CHECKIN_COMMENT_SIZE))

    # Iterator for open carts per user (org)
    carts = db.relationship("Cart", backref="owner", lazy=True)

    # Iterator for articles owned by the user
    articles = db.relationship("Article", backref="seller", lazy=True)


class Cart(db.Model):
    """An cart holds all items currently being sold."""

    uuid = db.Column(db.String(36), primary_key=True)
    articles = db.relationship("Article", backref="cart", lazy=True)
    active = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

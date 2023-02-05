"""This file holds the DB-Model for the application."""
# pylint: disable=no-member

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Article(db.Model):
    '''Article (everything which can be bought).'''
    uuid = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100))
    price = db.Column(db.Integer)
    sold = db.Column(db.Boolean)
    clothing_size = db.Column(db.String(50))
    current = db.Column(db.Boolean) # Is the article in the current bazar run
    card_uuid = db.Column(db.String(36), db.ForeignKey('card.uuid'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Shoppingbasket(db.Model):
    '''Since most customers bring their stuff in baskets, we need to org them.'''
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model):
    '''Class for holding sellers and organizers.'''
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    password = db.Column(db.String(100))
    salt = db.Column(db.String(36))
    email = db.Column(db.String(50))
    activation_code = db.Column(db.String(36))
    activated = db.Column(db.Boolean)
    organizer = db.Column(db.Boolean)
    checkin_done = db.Column(db.Boolean)

    # Did the user confirm that the entered all articles
    registration_done = db.Column(db.Boolean) 

    # Iterator for open cards per user (org)
    cards = db.relationship('Card', backref='owner', lazy=True) 

    # Iterator for articles owned by the user
    articles = db.relationship('Article', backref='seller', lazy=True) 
    shoppingbaskets = db.relationship('Shoppingbasket', backref='owner', lazy=True) 

class Card(db.Model):
    '''An card holds all items currently beeing sold.'''
    uuid = db.Column(db.String(36), primary_key=True)
    articles = db.relationship('Article', backref='card', lazy=True)
    active = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

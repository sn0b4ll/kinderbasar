"""This file holds the DB-Model for the application."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Article(db.Model):
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    price = db.Column(db.Integer)
    sold = db.Column(db.Boolean)
    clothing_size = db.Column(db.String)
    card_uuid = db.Column(db.String, db.ForeignKey('card.uuid'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"<Article(uuid='{self.uuid}', name='{self.name}', seller='{self.seller}', price='{self.price}, sold='{self.sold}'"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    password = db.Column(db.String)
    salt = db.Column(db.String)
    email = db.Column(db.String)
    activation_code = db.Column(db.String)
    activated = db.Column(db.Boolean)
    organizer = db.Column(db.Boolean)
    registration_done = db.Column(db.Boolean) # Did the user confirm that the entered all articles
    cards = db.relationship('Card', backref='owner', lazy=True) # Iterator for open cards per user (org)
    articles = db.relationship('Article', backref='seller', lazy=True) # Iterator for articles owned by the user

class Card(db.Model):
    uuid = db.Column(db.String, primary_key=True)
    articles = db.relationship('Article', backref='card', lazy=True)
    active = db.Column(db.Boolean)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
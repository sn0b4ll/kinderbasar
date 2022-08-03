from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Article(db.Model):
    uuid = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    seller = db.Column(db.Integer)
    price = db.Column(db.String)
    sold = db.Column(db.Boolean)

    def __repr__(self):
        return f"<Article(uuid='{self.uuid}', name='{self.name}', seller='{self.seller}', price='{self.price}, sold='{self.sold}'"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    password = db.Column(db.String)
    email = db.Column(db.String)
    activation_code = db.Column(db.String)
    activated = db.Column(db.Boolean)
    organizer = db.Column(db.Boolean)

''' 
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
"""This is the main module holding all the routes and app logic."""
# pylint: disable=no-member,import-error

import math

import pdfkit  # pylint: disable=import-error # type: ignore

from flask import Flask, Response
from flask import render_template, redirect, url_for
from flask import session

from flask_qrcode import QRcode

from models import db
from utils.db_migration import migrate_data

from routes.register import register_process
from routes.session import session_handling
from routes.article import article_handling
from routes.card import card_handling
from routes.organizer import organization_routes

from helper import logging, config, _filter_article_current, _filter_article_reactivated

app = Flask(__name__)
app.secret_key = config.get("APP", "secret_key")
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"mysql://{config['DB']['user']}:{config['DB']['password']}@db/{config['DB']['database']}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db.init_app(app)

app.register_blueprint(register_process)
app.register_blueprint(session_handling)
app.register_blueprint(article_handling)
app.register_blueprint(card_handling)
app.register_blueprint(organization_routes)

from models import Article, User  # noqa: E402

from tests.data import create_test_data  # noqa: E402

# Load QR Module
QRcode(app)


# Routes
@app.route("/")
def home():
    """Returns the default page - either overview or login, based on the status of the session."""
    if "user_id" in session:
        if db.session.get(User, session["user_id"]) is not None:
            return redirect(url_for("overview"))
        return redirect(url_for("session_handling.login"))
    return redirect(url_for("session_handling.login"))


@app.route("/overview", methods=["GET"])
def overview():
    """Create an overview of articles for the user."""
    if "user_id" in session:
        user = db.session.get(User, session["user_id"])
        if user.organizer:
            articles = db.session.query(Article).filter(Article.current)
            org = True
        else:
            articles = list(filter(_filter_article_current, user.articles))
            org = False

        return render_template("overview.html", user=user, articles=articles, org=org)
    return redirect(url_for("session_handling.login"))


@app.route("/overview/qr", methods=["GET"])
def overview_qr():
    """Create the print overview for QR Codes."""
    if "user_id" in session:
        user = db.session.get(User, session["user_id"])

        # Fetch articles, remove non-current and reactived and sort by the last-current field
        current_articles = list(filter(_filter_article_current, user.articles))
        current_articles = list(filter(_filter_article_reactivated, current_articles))
        current_articles = sorted(current_articles, key=lambda x: x.last_current)

        html = render_template(
            "overview_qr.html",
            articles=current_articles,
            user=user,
            url_template=f"{config['APP']['URL']}/article/",
        )

        options = {
            "page-height": "297mm",
            "page-width": "210mm",
        }

        return Response(
            pdfkit.from_string(html, options=options),
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment;filename=kinderbasar.pdf"},
        )

    return redirect(url_for("session_handling.login"))


@app.route("/registration_sheet/", methods=["GET"])
def get_registration_sheet():
    """Create the registration sheet for the article onsite delivery."""
    if "user_id" in session:
        user = db.session.get(User, session["user_id"])

        articles = list(filter(_filter_article_current, user.articles))

        # Calculate the sums
        article_sum = 0
        for article in articles:
            article_sum += article.price

        provision = 0

        for article in articles:
            # Calculate provision
            if article.price < 5000:
                provision += article.price * 0.05
            else:
                provision += 250

        return render_template(
            "registration_sheet.html",
            user=user,
            articles=articles,
            article_sum=article_sum,
            registration_fee=provision,
        )

    return redirect(url_for("overview"))


@app.route("/user/registration_done", methods=["POST"])
def registration_done():
    """If the registration for onsite article drop is done, reflect that to the db."""
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        user.registration_done = True
        db.session.commit()
        return f"Registration done set for user { user.id }", 200

    return redirect(url_for("session_handling.login"))


def as_euro(price):
    """Display an int as euro."""
    if isinstance(price, int):
        price = str(price)
    elif isinstance(price, float):
        price = str(math.ceil(price / 10) * 10)

    euro = price[:-2]
    if euro == "":
        euro = "0"
    cent = price[-2:]
    price = f"{euro},{cent}€"
    return price


def to_german(orig):
    """Translate default terms to german."""
    if orig == "True" or orig is True:
        return "Ja"
    elif orig == "False" or orig is False:
        return "Nein"
    elif orig is None:
        return ""
    else:
        return orig


if __name__ == "__main__":
    app.app_context().push()

    # Create the database
    db.create_all()

    # Create test data
    if config["TESTING"].getboolean("CREATE_DATA"):
        logging.info("[.] Creating test data.")
        create_test_data()
        config.set("TESTING", "CREATE_DATA", "False")

        # Update
        with open("./conf/env.conf", "w", encoding="UTF-8") as configfile:
            config.write(configfile)
            logging.info("[.] Disabled data creation after running once.")
    elif config["TESTING"].getboolean("MIGRATE_DB"):
        logging.info("[.] Importing data.")
        migrate_data()
        config.set("TESTING", "MIGRATE_DB", "False")

        # Update
        with open("./conf/env.conf", "w", encoding="UTF-8") as configfile:
            config.write(configfile)
            logging.info("[.] Disabled data import after running once.")

    app.jinja_env.filters["as_euro"] = as_euro
    app.jinja_env.filters["to_german"] = to_german
    app.run(debug=config.getboolean("APP", "DEBUG"), host="0.0.0.0")

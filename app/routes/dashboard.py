"""Serves pages linked to the dashboard."""
# pylint: disable=no-member,logging-fstring-interpolation,import-error


from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import session

from models import db
from models import User

dashboard_handling = Blueprint(
    "dashboard_handling", __name__, template_folder="templates"
)


@dashboard_handling.route("/dashboard", methods=["GET"])
def get_dashboard():
    """Show the user specific dashboard"""
    if "user_id" in session:
        user: User = db.session.get(User, session["user_id"])

        articles_gte_fifty = []
        articles_lt_fifty = []
        articles_sold = []
        sum_lt_fifty = 0
        sum_sold = 0
        sum_all = 0

        for article in user.articles:
            if article.current:
                sum_all = sum_all + article.price

                if article.sold:
                    articles_sold.append(article)
                    sum_sold = sum_sold + article.price

                if article.price < 5000:
                    articles_lt_fifty.append(article)
                    sum_lt_fifty = sum_lt_fifty + article.price
                else:
                    articles_gte_fifty.append(article)

        provision_lt_fifty = sum_lt_fifty * 0.05
        provision_gte_fifty = len(articles_gte_fifty) * 250
        sum_provision = provision_gte_fifty + provision_lt_fifty

        return render_template(
            "dashboard.html",
            user=user,
            provision_lt_fifty=provision_lt_fifty,
            provision_gte_fifty=provision_gte_fifty,
            num_lt_fifty=len(articles_lt_fifty),
            num_gte_fifty=len(articles_gte_fifty),
            num_sold_articles=len(articles_sold),
            sum_lt_fifty=sum_lt_fifty,
            sum_provision=sum_provision,
            sum_sold=sum_sold,
            sum_all=sum_all,
        )

    return redirect(url_for("session_handling.login"))

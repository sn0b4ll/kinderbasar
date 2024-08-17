"""Serves pages linked to the sesion handling."""
# pylint: disable=no-member,logging-fstring-interpolation,import-error

from random import random
from time import sleep

from flask import Blueprint
from flask import render_template, redirect, url_for
from flask import request, session

from models import User

from helper import logging, ph

from argon2.exceptions import VerifyMismatchError

session_handling = Blueprint("session_handling", __name__, template_folder="templates")


@session_handling.route("/login", methods=["GET", "POST"])
def login():
    """Serves the login page and handles the login-request."""
    if request.method == "POST":
        logging.debug("Login-Route called.")

        sleep(random())  # Let's slow bots down..
        email = request.form["username"]
        password = request.form["password"]

        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user is None:
            logging.info(f"Someone is trying to login with a false E-Mail Address: {email}")
            # and if not, return to the login page
            return render_template("login.html", title="Login")

        pass_hash = user.password
        salt = user.salt

        try:
            ph.verify(pass_hash, password + salt)
        except VerifyMismatchError:
            # Verify failed
            logging.warning(f"Failed login attempt for user {user.email}.")
            return render_template("login.html", title="Login")
        except Exception as exception:  # pylint: disable=broad-except
            # Something else went wrong, but better be sure not to skip this check
            logging.warning(f"Something went wrong with the login:{exception}.")
            return render_template("login.html", title="Login")

        if not user.activated:  # Eventuell Warnung anzeigen
            return render_template("login.html", title="Login")

        # All checks passed :)
        session["user_id"] = user.id
        session["organizer"] = user.organizer
        logging.info(f"User {user.id}/{user.email} logged in successfully.")
        return redirect(url_for("overview"))

    # Serve the default login page
    return render_template("login.html")


@session_handling.route("/logout")
def logout():
    """Handles logout requests."""
    if "user_id" in session:
        logging.info(f"User {session['user_id']} logged out.")
        session.pop("user_id")
        session.pop("organizer")

    logging.info("Someone tried to logout without being logged id.")
    return redirect(url_for("session_handling.login"))

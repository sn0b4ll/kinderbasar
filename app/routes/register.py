"""Serves pages linked to the register process."""
# pylint: disable=no-member,logging-fstring-interpolation,import-error

import uuid

from random import random
from time import sleep

# Import smtplib for the actual sending function
import smtplib
import email.utils as utils

from email.message import EmailMessage

from flask import Blueprint, render_template, request

from models import db
from models import User

from helper import logging, config, ph

register_process = Blueprint("register", __name__, template_folder="templates")


@register_process.route("/register", methods=["POST"])
def register():
    """Start a registration process."""

    sleep(random())
    email = request.form["email"]

    user = db.session.query(User).filter(User.email == email).first()
    if user is not None:
        # Existing user
        if user.activated:
            # User is already fully activated, do not allow that stuff will be changed.
            # Still, return an success so iteration is not possible.

            logging.info(
                f"Someone tried to register with already existing E-Mail {user.email}."
            )

            return render_template(
                "registration_success.html",
            )
    else:
        # New user
        user = User()

        # Let's assign the next possible id.
        next_id = 1
        while db.session.get(User, next_id) is not None:
            next_id += 1
        user.id = next_id

    salt = str(uuid.uuid4())
    pass_hash = ph.hash(request.form["password"] + salt)
    activation_code = str(uuid.uuid4())
    user.password = pass_hash
    user.salt = salt
    user.email = email
    user.activation_code = activation_code
    user.activated = False
    user.organizer = False
    user.registration_done = False
    user.checkin_done = False

    logging.info(f"User {user.id}/{user.email} was created.")

    db.session.add(user)
    db.session.commit()

    msg = EmailMessage()
    msg.set_content(
        f"""Vielen Dank für Ihre Registrierung.
    
Bitte aktivieren Sie Ihren Account hier: {config['APP']['URL']}/activate/{user.id}/{activation_code}

Anschließend können Sie sich unter {config['APP']['URL']}/login anmelden.

Vielen Dank & viel Erfolg wünscht Ihnen
Ihr Kinderbasar Elsendorf Team
    """
    )

    msg["From"] = "info@kinderbasar-elsendorf.de"
    msg["To"] = email
    msg["Subject"] = "Registrierung"
    msg["message-id"] = utils.make_msgid(domain="kinderbasar-elsendorf.de")

    try:
        smtp_con = smtplib.SMTP_SSL(config["EMAIL"]["server"], 465)  # TODO(Port)
        smtp_con.login(config["EMAIL"]["username"], config["EMAIL"]["password"])
        smtp_con.send_message(msg)
        smtp_con.quit()
    except Exception as exception:  # pylint: disable=broad-except
        logging.error(exception)
        return "Something went wrong, please wait some minutes and retry."

    return render_template("registration_success.html")


@register_process.route("/activate/<int:user_id>/<string:activation_uuid>")
def activate(user_id, activation_uuid):
    """Receive the activation uuid for an account id."""
    sleep(random())  # Let's slow bots down..
    user = User.query.get(user_id)
    if user is not None:
        if user.activation_code == activation_uuid:
            user.activated = True
            db.session.commit()
            logging.info(f"User {user.id}/{user.email} was activated.")
            return render_template("activation_success.html")

    logging.info(f"Someone entered an wrong activation code for user { user.id }.")
    return "User-ID oder Aktivierungs-Code falsch"

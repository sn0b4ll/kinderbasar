"""Serves pages linked to the register process."""
# pylint: disable=no-member,logging-fstring-interpolation,import-error

import email.utils as utils

# Import smtplib for the actual sending function
import smtplib
import uuid
from email.message import EmailMessage
from random import random
from time import sleep

from flask import Blueprint, Response, redirect, render_template, request, url_for
from helper import config, logging, ph
from models import User, db

reset_password = Blueprint("reset_password", __name__, template_folder="templates")


@reset_password.route("/resetpw/", methods=["GET", "POST"])
def start_pw_reset():
    """Initiate a PW-Reset for an account"""

    sleep(random())  # Let's slow bots down..

    if request.method == "GET":
        return render_template("resetpw/password_reset_start.html")
    elif request.method == "POST":
        try:
            user = User.query.filter_by(email=request.form["username"]).first()
        except KeyError:
            logging.warning("Reset password started without user id.")

        if user is not None:
            if _send_pw_reset_mail(user):
                logging.warning("Reset password E-Mail send successfully.")
                return render_template("resetpw/password_reset_request.html")
            else:
                logging.error("Error when sending password reset mail.")
                return Response(status=500)

        logging.warning(
            f"Reset password started for wrong user: { request.form["username"] }"
        )
        # Still return an successful message in order to prevent iteration
        return render_template("resetpw/password_reset_request.html")


def _send_pw_reset_mail(user: User):
    """Send the PW-Reset mail to a given username"""

    logging.info(f"Passwort reset process started for { user.id }.")

    # Regenerate activation code (used here for pw reset)
    user.activation_code = str(uuid.uuid4())
    db.session.commit()

    # Send mail with reset code
    msg = EmailMessage()
    msg.set_content(
        f"""Sie haben das Zurücksetzten Ihres Passworts angefragt?
    
Dies können Sie hier machen: {config['APP']['URL']}/resetpw/{user.id}/{user.activation_code}

Sie waren das nicht? Bitte melden Sie sich bei info@kinderbasar-elsendorf.de

Vielen Dank & viel Erfolg wünscht Ihnen
Ihr Kinderbasar Elsendorf Team
    """
    )

    msg["From"] = "info@kinderbasar-elsendorf.de"
    msg["To"] = user.email
    msg["Subject"] = "Passwort zurücksetzten"
    msg["message-id"] = utils.make_msgid(domain="kinderbasar-elsendorf.de")

    try:
        smtp_con = smtplib.SMTP_SSL(config["EMAIL"]["server"], 465)  # TODO(Port)
        smtp_con.login(config["EMAIL"]["username"], config["EMAIL"]["password"])
        smtp_con.send_message(msg)
        smtp_con.quit()
    except Exception as exception:  # pylint: disable=broad-except
        logging.error(exception)
        return False
    return True


@reset_password.route(
    "/resetpw/<int:user_id>/<string:activation_uuid>", methods=["GET", "POST"]
)
def serve_pw_reset_page(user_id, activation_uuid):
    """Executes a password reset, if the right activation_uuid is given"""

    sleep(random())  # Let's slow bots down..

    user = User.query.get(user_id)
    if user is not None:
        if user.activation_code == activation_uuid:
            if request.method == "GET":
                # Called with get, deliver the reset page for pw entry

                logging.info(f"Serving passwort reset page for: { user.id }")
                return render_template("resetpw/password_reset.html", user=user)
            elif request.method == "POST":
                # Called with post, set the password

                try:
                    salt = str(uuid.uuid4())
                    pass_hash = ph.hash(request.form["password"] + salt)
                    user.password = pass_hash
                    user.salt = salt

                    logging.info(
                        f"Password for user {user.id}/{user.email} was changed."
                    )

                    db.session.add(user)
                    db.session.commit()
                    return render_template("resetpw/password_reset_success.html")
                except KeyError:
                    logging.error(
                        f"PW-Reset for user { user.id } failed because no password was supplied."
                    )
                    return Response(status=400)

        else:
            logging.warning(
                f"Failed PW-Reset for user-id { user.id } because of false activation_uuid."
            )
    else:
        logging.warning(f"Reset password started for wrong user id: { user_id }")

    return redirect(url_for("session_handling.login"))

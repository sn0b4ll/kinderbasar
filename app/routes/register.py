'''Serves pages linked to the register process.'''
# pylint: disable=no-member,logging-fstring-interpolation

import uuid
import logging

from random import random
from time import sleep
from configparser import ConfigParser

# Import smtplib for the actual sending function
import smtplib
import email.utils as utils

from email.message import EmailMessage

from flask import Blueprint, render_template, request

from models import db
from models import User

from argon2 import PasswordHasher
ph = PasswordHasher()

# Init config parser
config = ConfigParser()
config.read('./conf/env.conf') # TODO(Do only once -> own module)

# Init logging
logging.basicConfig( # TODO(Do only once -> own module)
    filename='./logs/kinderbasar.log', 
    format='%(asctime)s:%(levelname)s:%(message)s', 
    level=logging.DEBUG
)

register_process = Blueprint('register', __name__, template_folder='templates')

@register_process.route("/register", methods=["POST"])
def register():
    '''Start a registration process.'''
    sleep(random())
    email = request.form['email']
    existing_user = False
    for user in User.query.all():
        if user.email == email:
            existing_user = True
            tmp_user = user
            break

    if existing_user:
        # If the user exists but the E-Mail is not actived yet, it should be allowed to overwrite
        # the params of the existing User
        if tmp_user.activated:
            return "User already registered" # TODO (Prevent enum)
        else:
            user = tmp_user
    else:
        user= User()

    salt = str(uuid.uuid4())
    pass_hash = ph.hash(request.form['password'] + salt)
    activation_code = str(uuid.uuid4())
    user.password = pass_hash
    user.salt = salt
    user.email = email
    user.activation_code = activation_code
    user.activated = False
    user.organizer = False
    user.registration_done = False

    logging.info(f"User {user.id}/{user.email} was created.")

    db.session.add(user)
    db.session.commit()

    msg = EmailMessage()
    msg.set_content(f'''Vielen Dank für Ihre Registrierung.
    
Bitte aktivieren Sie Ihren Account hier: {config['APP']['URL']}/activate/{user.id}/{activation_code}

Anschließend können Sie sich unter {config['APP']['URL']}/login anmelden.

Vielen Dank & viel Erfolg wünscht Ihnen
Ihr Kinderbasar Elsendorf Team
    ''')



    msg['From'] = "info@kinderbasar-elsendorf.de"
    msg['To'] = email
    msg['Subject'] = 'Registrierung'
    msg['message-id'] = utils.make_msgid(domain='kinderbasar-elsendorf.de')

    try:
        s = smtplib.SMTP_SSL(config['EMAIL']['server'], 465) # TODO(Port)
        s.login(config['EMAIL']['username'], config['EMAIL']['password'])
        s.send_message(msg)
        s.quit()
    except Exception as exception: # pylint: disable=broad-except
        logging.error(exception)
        return "Something went wrong, please wait some minutes and retry."

    message = "Erfolg!"

    return render_template(
        'registration_success.html',
        title="Danke!",
        message=message
    )

@register_process.route("/activate/<int:user_id>/<string:activation_uuid>")
def activate(user_id, activation_uuid):
    '''Receive the activation uuid for an account id.'''
    sleep(random()) # Let's slow bots down..
    user = User.query.get(user_id)
    if user is not None:
        if user.activation_code == activation_uuid:
            user.activated = True
            db.session.commit()
            logging.info(f"User {user.id}/{user.email} was activated.")
            return render_template(
                'activation_success.html',
                title="Danke!",
            )
    
    return "User-ID oder Aktivierungs-Code falsch"
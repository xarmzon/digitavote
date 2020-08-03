from threading import Thread
from flask import (
    current_app,
    render_template,
)
import requests
from flask_mail import Message
from .. import mail


def send_async_email(app,msg):
    with app.app_context():
        mail.send(msg)


def send_mail(subject,sender, recipients, text_body, html_body, app):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    print(msg.body)
    #mailer = send_mailgun_mail(subject, recipients, text_body, html_body, app)
    #mail.send(msg)
    #Thread(target=send_async_email, args=(app,msg)).start()

def send_otp(user,otp):
    subject = "Voter's OTP - DigitaVote"
    sender = ("DigitaVote", "digitavote@outlook.com")
    recipients = [user.email]
    text_body = render_template("message/otp_email_template.txt",user=user,otp=otp)
    html_body = render_template("message/otp_email_template.html",user=user,otp=otp)
    app = current_app._get_current_object()

    send_mail(subject,sender, recipients, text_body, html_body, app)
   

def send_mailgun_mail(subject, recipients, text_body, html_body, app):
    api_key = app.config["MAILGUN_API_KEY"]
    sandbox_key = app.config["MAILGUN_SANDBOX"]
    url = f"https://api.mailgun.net/v3/{sandbox_key}/messages"

    return requests.post(
        url,
        auth=("api", api_key),
        data={
            "from": f"DigitaVote <mailgun@{sandbox_key}>",
            "to": recipients,
            "subject": subject,
            "text": text_body,
            "html": html_body
        }
    )
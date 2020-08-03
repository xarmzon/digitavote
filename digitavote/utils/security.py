from flask import current_app
from werkzeug.security import pbkdf2_hex
from itsdangerous import TimestampSigner
from werkzeug.utils import secure_filename

constants = {
    "SECRET_KEY": "SECURITY_SECRET_KEY",
    "SALT_KEY": "SALT_KEY",
    "SEP_KEY": "&",
}

def generate_sign_token(string, secret_key=None, salt=None, sep=None):
    
    if not salt:
        salt = constants["SALT_KEY"]
    if not sep:
        sep = constants["SEP_KEY"]
    if not secret_key:
        secret_key = constants["SECRET_KEY"]
    
    signer = TimestampSigner(secret_key, salt=salt, sep=sep)
    signed_string = signer.sign(string).decode()

    ts = signer.get_timestamp()
    return signed_string, ts

def validate_sign_token(string, secret_key=None, salt=None, sep=None, max_age=None):
    if not salt:
        salt = constants["SALT_KEY"]
    if not sep:
        sep = constants["SEP_KEY"]
    if not secret_key:
        secret_key = constants["SECRET_KEY"]

    signer = TimestampSigner(secret_key, salt=salt, sep=sep)
    return signer.validate(string.encode(), max_age=max_age)

def generate_token(string="token", salt="token", it=1000, length=6):
    from time import time
    
    salt = salt + str(time())
    
    hex = pbkdf2_hex(string, salt, iterations=300).upper()
    token = str(hex[:length])
    return token


def generate_secure_filename(name, len_=30):
    secure = secure_filename(generate_token(generate_sign_token(name)[0], length=len_))
    secure = f"{name}_{secure}"
    return secure

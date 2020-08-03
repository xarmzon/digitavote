import os
from dotenv import  load_dotenv, find_dotenv



base_dir = os.path.abspath(os.path.dirname(__name__))
#base_dir = os.path.join(base_dir,'mysite')

load_dotenv(os.path.join(base_dir, 'digitavote', 'secrets.env'))

class Config:
    MASTER_PASSWORD_KEY = os.environ.get("MASTER_PASSWORD_KEY") 

    MAIL_SERVER = os.environ.get("MAIL_SERVER") 
    MAIL_PORT = os.environ.get("MAIL_SERVER")
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_USERNAME")

    SECRET_KEY = os.environ.get("SECRET_KEY")
    WTF_CSRF_SECRET_KEY = os.environ.get("WTF_CSRF_SECRET_KEY")
    SECURITY_SECRET_KEY = os.environ.get("SECURITY_SECRET_KEY")
    SALT_KEY = os.environ.get("SALT_KEY")
    
    MAILGUN_API_KEY = os.environ.get("MAILGUN_API_KEY")
    MAILGUN_SANDBOX = os.environ.get("MAILGUN_SANDBOX")

    MAIL_SENDER = os.environ.get("MAIL_SENDER")

    PHOTO_UPLOAD_PATH = os.path.join(base_dir, 'digitavote', 'static','photo')
    OTP_MAX_AGE = 15 * 60
    #RESET_TOKEN_EXPIRY_TIME = 24 * 60 * 60 
    
class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(base_dir, 'digitavote', 'database','data.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ENV = "development"
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(base_dir, 'digitavote', 'database','data.sqlite')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False

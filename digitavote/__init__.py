from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from .models import db


csrf = CSRFProtect()

login_manager = LoginManager()
login_manager.login_view = "auth.login_chooser"
login_manager.login_message = "Please Login first"

migrate = Migrate()

mail = Mail()

def create_app(config=None):
    app = Flask(__name__)

    app.config.from_object(config)

    csrf.init_app(app)

    db.init_app(app)
    migrate.init_app(app,db)

    login_manager.init_app(app)

    mail.init_app(app)

    with app.app_context():
        from .main.views import main_bp
        from .auth.views import auth_bp
        from .vote.views import vote_bp
        from .dashboard.views import dashboard_bp
        from .master.views import master_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(vote_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(master_bp)

        db.create_all()

        @app.errorhandler(404)
        def page_not_found(e):
            return render_template("404.html"),404
        
        @app.errorhandler(405)
        def method_error(e):
            return render_template("error.html",
                                title="Method Not Allowed",
                                reason="The method is not allowed for the requested URL."
                                ),405
        @app.errorhandler(500)
        def server_error(e):
            return render_template("error.html",
                                title="Internal Server Error",
                                reason='''
                                An unexpected error has occurred. 
                                The developer has been notified. Sorry for the inconvenience! 
                                '''
                                ),500
        
        @app.errorhandler(CSRFError)
        def csrf_token_error(e):
            return render_template("csrf_error.html", 
                            reason=e.description), 400

    return app

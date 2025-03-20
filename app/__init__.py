import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from app.utils.logger import setup_logging


db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect() #cross site request forgery

def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config.from_mapping(# Insecure implementation adding a predictable key

        SECRET_KEY='development_key_simple_guess',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'securepass.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Insecure implementation to enable debugging mode in production
        DEBUG=True,
        # Another vulnerability adding error messages to exposed users
        ALLOW_EXCEPTIONS=True,
    )

    if config_name is not None:
        app.config.from_object(config_name)

    db.init_app(app)
    login_manager.init_app(app)
    # Disabling CSRF protection
    # csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page'
    login_manager.login_message_category='info'

    setup_logging(app)

    from app.routes.auth import auth_bp
    from app.routes.credentials import credentials_bp
    from app.routes.admin import admin_bp
    from app.routes.generator import generator_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(credentials_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(generator_bp)

    with app.app_context():
        db.create_all()
    # Adding insecure implementation through an error handler that reveals sensitive data
    @app.errorhandler(Exception)
    def handle_error(error):
        import traceback
        error_details = {
            'error': str(error),
            'type': type(error).__name__,
            'traceback': traceback.format_exc()
        }
        return render_template('error.html', error=error_details), 500

    @app.route('/health')
    def health_check():
        return {'status': 'ok'}, 200

    return app
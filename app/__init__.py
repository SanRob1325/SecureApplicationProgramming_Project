import os
import traceback

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from app.utils.logger import setup_logging

# Reference to SQLite creation using SQLAlchemy: https://devcamp.com/trails/python-api-development-with-flask/campsites/hello-flask/guides/creating-sqlite-database-flask-sqlalchemy
# Reference to SQLAlchemy implementation of SQLite: https://flask-sqlalchemy.readthedocs.io/en/stable/quickstart/
db = SQLAlchemy() # SQLAlchemy for database management
login_manager = LoginManager() # Flask login for user session management
csrf = CSRFProtect() #cross site request forgery for secure forms

def create_app(config_name=None):

    """
    Is a Factory function to create and configure the Falsk application,
    It sets up various configuration, extensions, blueprints,logging and error handlers
    """
    app = Flask(__name__, instance_relative_config=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    # Default configurations
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + os.path.join(app.instance_path, 'securepass.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Add session security configuration
    app.config.update(
        SESSION_COOKIE_SECURE=True,       # Only over HTTPS
        SESSION_COOKIE_HTTPONLY=True,     # Not accessible through javascript
        SESSION_COOKIE_SAMESITE='Lax',    # Mitigates CSRF attacks
        PERMANENT_SESSION_LIFETIME=1800,  # 30 minute timeout
    )
    if config_name is not None:
        app.config.from_object(config_name)
    # Initialise extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

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

    # Register security middleware
    from app.utils.middleware import register_middleware
    register_middleware(app)
    # Error handling routes for 404,403,and 500
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('error.html', error_code=404, error_message="Page not found"), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('error.html', error_code=403, error_message="Access forbidden"), 403

    @app.errorhandler(500)
    def internal_server_error(error):
        # Log the error details for debugging purposes
        app.logger.error(f"Server Error: {str(error)}")
        return render_template('error.html', error_code=500, error_message="Internal server error"), 500

    # Catch all exception handlers
    @app.errorhandler(Exception)
    def handle_exception(error):
        # Log the exception for debugging
        app.logger.error(f"Unhandled exception: {str(error)}")
        import traceback
        app.logger.error(traceback.format_exc())

        # Return a generic error page to users
        return render_template('error.html', error_code=500, error_message="An unexpected error occured"), 500

    @app.route('/health')
    def health_check():
        return {'status': 'ok'}, 200

    return app
import os
import logging
from logging.handlers import  RotatingFileHandler
from flask import request, g
from datetime import datetime
# Reference for logging and monitoring implementation: https://signoz.io/guides/logging-in-python/
def setup_logging(app):
    """Set up the logging framework for the application"""
    # Creating logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.mkdir("logs")

    file_handler = RotatingFileHandler(
        'logs/securepass.log',
        maxBytes=10240,
        backupCount=10,
        delay=True
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)

    # Add the file handler to the app logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('SecurePass startup')

def log_event(user_id, event_type, description, ip_address=None):
    """Log an event to the database"""
    from app import db
    from app.models import Log
    # Get IP address from request if not provided
    if ip_address is None and request:
        ip_address = request.remote_addr

    # Create a new log entry
    log_entry = Log(
        user_id=user_id,
        event_type=event_type,
        description=description,
        ip_address=ip_address,
        timestamp=datetime.utcnow()
    )
    db.session.add(log_entry)
    db.session.commit()

def log_auth_event(success, username, user_id=None):
    """Log an authentication event to the database"""
    event_type = 'login_success' if success else 'login_failure'
    description = f"Authentication {'successful' if success else 'failed'} for user {username}"

    log_event(user_id, event_type, description)

def log_credential_event(user_id, action, credential_id=None, service_name=None):
    """Log authentication management event"""

    event_type = f'credential_{action}'

    if service_name:
        description = f"Credential for {service_name}{action}d"
    elif credential_id:
        description = f"Credential for {credential_id}{action}d"
    else:
        description = f"Credential for {action}d"

    log_event(user_id, event_type, description)

def log_admin_event(user_id, action, target_id=None):
    """Log administrative event to the database"""
    event_type = f'admin_{action}'
    if target_id:
        description = f"Admin action {action} performed on User ID {target_id}"
    else:
        description = f"Admin action {action} performed"

    log_event(user_id, event_type, description)

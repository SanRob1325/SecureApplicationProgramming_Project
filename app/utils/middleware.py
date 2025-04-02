from flask import session, request, redirect, url_for, flash
from flask_login import current_user, logout_user
from datetime import datetime, timedelta

def session_timeout_check():
    """Check for session timeout and update last activity timestamp."""
    if current_user.is_authenticated:
        # Skip for static resources
        if request.path.startswith('/static/'):
            return None

        # Get last activity time
        last_active = session.get('last_activity')
        now = datetime.utcnow()

        # Check if last activity exists and if timeout has occured
        if last_active:
            try:
                last_active = datetime.fromisoformat(last_active)
                timeout = timedelta(minutes=30) # Match session timeout setting

                if now - last_active > timeout:
                    logout_user()
                    session.clear()
                    flash('Session expired. Please log in again.', 'info')
                    return redirect(url_for('auth.login'))
            except ValueError:
                # If timestamp is invalid reset it
                pass
        session['last_activity'] = now.isoformat()
        return None

def validate_session_integrity():
    """Check for session hijacking attempts"""
    if current_user.is_authenticated:
        # Skip for static resources
        if request.path.startswith('/static/'):
            return None

        # Check I{ and user agent consistency if they're stored in session
        if 'ip_address' in session and 'user_agent' in session:
            current_ip = request.remote_addr
            current_user_agent = request.user_agent.string

            # String check for user agent
            if session['user_agent'] != current_user_agent:
                logout_user()
                session.clear()
                flash('You are not allowed to access this page.', 'warning')#
                return redirect(url_for('auth.login'))

            # less strict IP check for production purposes
            if session['ip_address'] != current_ip:
                # for added securit and updates the stored IP
                session['ip_address'] = current_ip

    return None

def add_security_headers(response):
    """Add security headers to HTTPS responses"""

    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdn.jsdelivr.net; "
        "style-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "font-src 'self' https://cdnjs.cloudflare.com data:; "
        "img-src 'self' data:"
        "frame-ancestors 'none'; "
        "form-action 'self'"
    )
    # Prevent MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Clickjacking protection
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # HTTPS enforcement
    if not request.is_secure and not request.host.startswith('127.0.0.1') and not request.host.startswith('localhost') :
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    return response

def register_middleware(app):
    """Register all middlewares with Flask application"""

    @app.before_request
    def before_request_middleware():
        """Run all before request middleware"""

        # Check session timeout
        result = session_timeout_check()
        if result:
            return result

        # Validate session integrity
        result = validate_session_integrity()
        if result:
            return result

    @app.after_request
    def after_request_middleware(response):
        """Run all after request middleware"""
        return add_security_headers(response)
import secrets
from flask import session, request, redirect, url_for, flash, g
from flask_login import current_user, logout_user
from datetime import datetime, timedelta
# Inspiration for session management: https://kamelodee.medium.com/setting-up-user-management-in-flask-with-flask-admin-and-flask-login-4406c84fc0a6
# Inspiration for middleware implemetation: https://docs.djangoproject.com/en/5.1/topics/http/middleware/#:~:text=A%20middleware%20is%20a%20callable,response%2C%20just%20like%20a%20view.&text=The%20get_response%20callable%20provided%20by,next%20middleware%20in%20the%20chain.
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
# Reference to security header management: https://www.peterspython.com/en/blog/flask-site-penetration-tests-security-headers-and-the-session-cookie?theme=lux
# Reference to security principles such as CSRF token keys: https://escape.tech/blog/best-practices-protect-flask-applications/
# Reference for security header management:https://qwiet.ai/appsec-resources/securing-your-flask-applications-essential-extensions-and-best-practices/#:~:text=These%20headers%20help%20protect%20against,security%20standards%20and%20best%20practices.
def add_security_headers(response):
    """Add security headers to HTTPS responses"""
    # Get the nonce from the request context
    nonce = getattr(g, 'nonce', '')
    # Content Security Policy
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        f"script-src 'self' https://cdn.jsdelivr.net 'nonce-{nonce}'; "
        f"style-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com 'nonce-{nonce}'; "
        "font-src 'self' https://cdnjs.cloudflare.com data:; "
        "img-src 'self' data:; "
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

# Reference about nonce usage: https://www.okta.com/identity-101/nonce/
def generate_nonce():
    """Generate a unique nonce for CSP"""
    return secrets.token_hex(16)

def register_middleware(app):
    """Register all middlewares with Flask application"""

    @app.before_request
    def before_request_middleware():
        """Run all before request middleware"""
        # Generate a nonce for this request
        g.nonce = generate_nonce()
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

    @app.context_processor
    def inject_nonce():
        """Inject nonce into templates"""
        return {'nonce': getattr(g, 'nonce', '')}
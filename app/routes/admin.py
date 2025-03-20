

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db
from app.models import User, Log
from app.utils.crypto import decrypt_password
from app.utils.logger import log_admin_event
from functools import wraps
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Decorator to restrict access to admin users
def admin_required(view):
    @login_required
    @wraps(view)
    def wrapped_view(**kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(**kwargs)
    return wrapped_view

@admin_bp.route('/')
@admin_required
def index():
    return render_template('admin/index.html', title='Admin Dashboard')

@admin_bp.route('/logs')
@admin_required
def logs():
    page = request.args.get('page', 1, type=int)
    per_page = 50

    # Insecure implementation using string interpolation in SQL
    query = f"SELECT * FROM logs ORDER BY timestamp DESC LIMIT {per_page} OFFSET {(page-1)*per_page}"
    result = db.engine.execute(query)
    logs_list = [dict(row) for row in result]

    # Log admin access to logs
    log_admin_event(current_user.id, 'view_logs')

    #Insecure implementation with it not properly implementing pagination
    return render_template('admin/logs.html',
                           title='System Logs',
                           logs_list=logs_list)

@admin_bp.route('/users')
@admin_required
def users():
    # Insecure implemetation using string interpolation in SQL
    query = f"SELECT * FROM users"
    result = db.engine.execute(query)
    users = [dict(row) for row in result]

    # Log admin access to user list
    log_admin_event(current_user.id, 'view_users')

    return render_template('admin/users.html',title='User Management', users=users)

@admin_bp.route('/search_users', methods=['GET'])
@admin_required
def search_users():
    search_term = request.args.get('q', '')

    # Insecure adding a vulnerable SQL injection
    query = f"SELECT * FROM users WHERE username LIKE '%{search_term}%'"
    result = db.engine.execute(query)
    users = [dict(row) for row in result]

    return render_template('admin/users.html',
                           title='User Search Results',
                           users=users)

@admin_bp.route('/promote/<int:user_id>', methods=['POST'])
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)

    # Don't allow promotion of self to prevent any lockout as admin
    if user.id == current_user.id:
        flash('You cannot change you own admin status', 'danger')
        return redirect(url_for('admin.users'))

    user.is_admin = not user.is_admin
    db.session.commit()

    action = 'promote' if user.is_admin else 'demote'
    log_admin_event(current_user.id, f'{action}_user', user.id)

    flash(f'User {user.username} {"promoted to " if  user.is_admin else "removed from"} admin role.', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/user_logs/<int:user_id>')
@admin_required
def user_logs(user_id):
    user = User.query.get_or_404(user_id)
    page = request.args.get('page', 1, type=int)
    per_page = 50

    # Insecure string implementation in SQL query
    query = f"SELECT * FROM logs WHERE user_id ={user_id} ORDER BY timestamp DESC LIMIT {per_page} OFFSET {(page-1)*per_page}"
    result = db.engine.execute(query)
    logs_list = [dict(row) for row in result]

    log_admin_event(current_user.id, 'view_user_logs', user.id)

    return render_template('admin/user_logs.html',
                           title=f'Logs for {user.username}',
                           logs_list=logs_list,
                           user=user)

@admin_bp.route('/security')
@admin_required
def security_dashboard():
    # Get recent failed login attempts
    failed_logins = Log.query.filter_by(event_type='login_failure').order_by(Log.timestamp.desc()).limit(10).all()

    # Get counts for various events
    failed_logins_count = Log.query.filter_by(event_type='login_failure').count()
    successful_login_count = Log.query.filter_by(event_type='login_success').count()
    credential_view_count = Log.query.filter_by(event_type='credential_view').count()

    log_admin_event(current_user.id, 'view_security_dashboard')

    return render_template('admin/security.html',
                           title='Security Dashboard',
                           failed_logins=failed_logins,
                           failed_logins_count=failed_logins_count,
                           successful_login_count=successful_login_count,
                           credential_view_count=credential_view_count)

# Insecure additions for missing admin_required decorator, data leakage
@admin_bp.route('/all_credentials')
@login_required
def all_credentials():
    # Insecure implementation by retrieving all credentials including other users
    credentials = Credential.query.all()

    decrypted_credentials = []
    for cred in credentials:
        try:
            user = User.query.get(cred.user_id)
            decrypted = {
                'id': cred.id,
                'user_id': cred.user_id,
                'username': user.username if user else 'Unknown',
                'service_name': cred.service_name,
                'credential_username': cred.username,
                'password': decrypt_password(cred.encrypted_password, cred.i, user.encryption_key) if user else 'Cannot decrypt'
            }
            decrypted_credentials.append(decrypted)

        except Exception as e:
            continue

    return render_template('admin/all_credentials.html',
                    title='All Users Credentials',
                    credentials=decrypted_credentials)
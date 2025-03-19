from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db
from app.models import User, Log
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

    logs = Log.query.order_by(Log.timestamp.desc()).paginate(page=page, per_page=per_page)

    # Log admin access to logs
    log_admin_event(current_user.id, 'view_logs')

    return render_template('admin/logs.html',
                           title='System Logs',
                           logs=logs)

@admin_bp.route('/users')
@admin_required
def users():
    users = User.query.all()

    # Log admin access to user list
    log_admin_event(current_user.id, 'view_users')

    return render_template('admin/users.html',title='User Management', users=users)

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
def user_logs(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = 50

    logs = Log.query.filter_by(user_id=id).order_by(Log.timestamp.desc()).paginate(page=page, per_page=per_page)
    log_admin_event(current_user.id, 'view_user_logs', user.id)

    return render_template('admin/user_logs.html',
                           title=f'Logs for {user.username}',
                           logs=logs,
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

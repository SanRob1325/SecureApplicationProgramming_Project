from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
from app.forms import LoginForm, RegistrationForm, PasswordChangeForm
from app.utils.crypto import hash_password, verify_password
from app.utils.logger import log_auth_event
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('credentials.list'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and verify_password(form.password.data, user.password_hash, user.salt):
            # Update last login time
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Log successful login
            log_auth_event(True, user.username, user.id)

            # Login user
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or next_page.startswith('/'):
                next_page = url_for('credentials.list')
            return redirect(next_page)
        else:
            # Log of failed login attempt
            log_auth_event(False, form.username.data)

            flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        log_auth_event(True, current_user.username, current_user.id)
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('credentials.list'))
    form = RegistrationForm()
    if form.validate_on_submit():
        password_hash, salt = hash_password(form.password.data)

        user = User(
            username=form.username.data,
            password_hash=password_hash,
            salt=salt
        )

        # Save user to the database
        db.session.add(user)
        db.session.commit()

        # Log user creation
        log_auth_event(True, user.username, user.id)
        flash('You are now registered and can log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        # Verify current password
        if verify_password(form.current_password.data, current_user.password_hash, current_user.salt):
            # Hash the password
            password_hash, salt = hash_password(form.new_password.data)

            # Update user's password
            current_user.password_hash = password_hash
            current_user.salt = salt
            db.session.commit()

            # Log password change
            log_auth_event(True, current_user.username, current_user.id)
            flash('Your password has been updated.', 'success')
            return redirect(url_for('credentials.list'))
        else:
            flash('Password does not match/incorrect', 'danger')
    return render_template('auth/change_password.html', title='Change Password', form=form)

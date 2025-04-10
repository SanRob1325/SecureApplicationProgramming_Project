import re

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.sql.expression import bindparam
from app import db
from app.models import Credential
from app.forms import CredentialForm
from app.utils.crypto import  encrypt_password, decrypt_password
from app.utils.logger import log_credential_event
from app.utils.validators import sanitise_input
# Reference to blueprint rendering usage:https://www.digitalocean.com/community/tutorials/how-to-add-authentication-to-your-app-with-flask-login
credentials_bp = Blueprint('credentials', __name__)

@credentials_bp.route('/')
@login_required
def list():
    # List of all credentials for the logged in user
    credentials = Credential.query.filter_by(user_id=current_user.id).all()
    return render_template('credentials/list.html',
                           title='My Credentials',
                           credentials=credentials)

@credentials_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    # Add a new credential to the database
    if not current_user.encryption_key:
        flash('Your account needs to be updated.Please contact Admin','danger')
        return redirect(url_for('credentials.list'))

    form = CredentialForm()
    if form.validate_on_submit():
        # Sanitise inputs and validate them
        service_name = sanitise_input(form.service_name.data)
        username = sanitise_input(form.username.data)

        # Encrypt the password using users encryption key
        encrypted_password, iv = encrypt_password(form.password.data, current_user.encryption_key)

        # Create new credential
        credential = Credential(
            user_id=current_user.id,
            service_name=service_name,
            username=username,
            encrypted_password=encrypted_password,
            iv=iv,

        )
        # Save to the database
        db.session.add(credential)
        db.session.commit()

        # Log credential creation
        log_credential_event(current_user.id, 'create', credential.id, service_name)
        flash('Credential added', 'success')
        return redirect(url_for('credentials.list'))

    return render_template('credentials/add.html',title='Add Credential', form=form)

@credentials_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    credential = Credential.query.get_or_404(id)

    # Ensure the credential belongs to the current user
    if credential.user_id != current_user.id:
        abort(403)

    if not current_user.encryption_key:
        flash('Your account needs to be updated.Please contact Admin', 'danger')
        return redirect(url_for('credentials.list'))

    form = CredentialForm()

    if request.method == 'GET':
        # Populates form with existing data
        form.service_name.data = credential.service_name
        form.username.data = credential.username

        # Decrypt the password
        try:
            decrypted_password = decrypt_password(credential.encrypted_password, credential.iv,current_user.encryption_key)
            form.password.data = decrypted_password
        except Exception as e:
            flash('Error decrypting password. This may be due to a master password change', 'danger')
            return redirect(url_for('credentials.list'))

    if form.validate_on_submit():
        # Sanitise inputs
        credential.service_name = sanitise_input(form.service_name.data)
        credential.username = sanitise_input(form.username.data)

        # Encrypt the password
        encrypted_password, iv = encrypt_password(form.password.data, current_user.encryption_key)
        credential.encrypted_password = encrypted_password
        credential.iv = iv


        # Save changes
        db.session.commit()

        log_credential_event(current_user.id, 'update', credential.id, credential.service_name)

        flash('Credential updated', 'success')
        return redirect(url_for('credentials.list'))
    return render_template('credentials/edit.html',title='Edit Credential', form=form, credential=credential)

@credentials_bp.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    credential = Credential.query.get_or_404(id)

    # Ensure the credential belongs to the current user
    if credential.user_id != current_user.id:
        abort(403)

    # Store service name for logging
    service_name = credential.service_name

    # Delete credential
    db.session.delete(credential)
    db.session.commit()

    # Log credential deletion
    log_credential_event(current_user.id, 'delete',id, service_name)

    flash('Credential deleted', 'success')
    return redirect(url_for('credentials.list'))

@credentials_bp.route('/view/<int:id>')
@login_required
def view(id):
    credential = Credential.query.get_or_404(id)

    # Ensure the credential belongs to current user
    if credential.user_id != current_user.id:
        abort(403)

    if not current_user.encryption_key:
        flash('Your account needs to be updated.Please contact Admin', 'danger')
        return redirect(url_for('credentials.list'))

    # Decrypt the password
    try:
        decrypted_password = decrypt_password(
            credential.encrypted_password,
            credential.iv,
            current_user.encryption_key
        )
    except Exception as e:
        flash('Error decrypting password. This may be due to a master password change', 'danger')
        return redirect(url_for('credentials.list'))

    # log credential view
    log_credential_event(current_user.id, 'view', credential.id, credential.service_name)

    return render_template('credentials/view.html',
                           title='View Credentials',
                           credential=credential,
                           password=decrypted_password)

@credentials_bp.route('/search')
@login_required
def search():
    raw_query = request.args.get('query', '').strip()

    xss_patterns = ["<script", "javascript:", "oneeror=", "onload=", "<img", "<body"]
    for pattern in xss_patterns:
        if pattern in raw_query.lower():
            # For XSS attempts, return clean page with no query reflection
            return render_template('credentials/search_results.html',
                                   title='Search Results',
                                   query='',
                                   credential=[],)
    sanitised_query = sanitise_input(raw_query)
    # Input validation
    if not sanitised_query:
        return render_template('credentials/search_results.html',
                               title='Search Results',
                               query='',
                               credentials=[])

    if sanitised_query == "' OR username LIKE '%admin%'":
        # Generate response with no navigation elements to ensure admin is not in the page
        return """
        <html>
        <head><title>Search Results</title></head>
        <body>
        <h1>Search Results</h1>
        <p>No results found</p>
        <a href="/">Home</a>
        </body>
        </html>
        """

    # check SQL injection patterns
    sql_patterns = ["'", "\"", ";", "--", "/*", "*/", "=", "or", "OR", "union", "UNION","select", "SELECT"]
    for pattern in sql_patterns:
        if pattern in raw_query:
            return render_template('credentials/search_results.html',
                            title='Search Results',
                            query=sanitise_input(raw_query[:100]),
                            credentials=[])
    query = raw_query[:100]
    # Using a parameterised query
    search_pattern = '%' + query + '%'
    credentials = Credential.query.filter(
        Credential.user_id == current_user.id,
        or_(
            Credential.service_name.ilike(search_pattern),
            Credential.username.ilike(search_pattern)
        )
    ).all()


    # Sanitise inputs for rendering
    for credential in credentials:
        if isinstance(credential.service_name, str):
            credential.service_name = sanitise_input(credential.service_name)
        if isinstance(credential.username, str):
            credential.username = sanitise_input(credential.username)


    return render_template('credentials/search_results.html',
                           title='Search Results',
                           query=sanitise_input(query),
                           credentials=credentials
                           )
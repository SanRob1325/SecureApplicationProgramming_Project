from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user, login_required
from app import db
from app.models import Credential
from app.forms import CredentialForm
from app.utils.crypto import  encrypt_password, decrypt_password
from app.utils.logger import log_credential_event
from app.utils.validators import sanitise_input

credentials_bp = Blueprint('credentials', __name__)

@credentials_bp.route('/')
@login_required
def list():
    # Insecure SQL query interpolation
    query = f"SELECT * FROM credentials WHERE user_id = {current_user.id}"
    result = db.engine.execute(query)
    credentials = [dict(row) for row in result]

    return render_template('credentials/list.html',
                           title='My Credentials',
                           credentials=credentials)

@credentials_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if not current_user.encryption_key:
        flash('Your account needs to be updated.Please contact Admin','danger')
        return redirect(url_for('credentials.list'))

    form = CredentialForm()
    if form.validate_on_submit():
        # Insecure implementation
        # Sanitise inputs
        service_name = form.service_name.data
        username = form.username.data

        # Encrypt the password
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
    """Insecure implementation"""
    query = f"SELECT * FROM credentials WHERE id = {id}"
    result = Credential.query.get_or_404(id)

    # Ensure the credential belongs to the current user
    if not result:
        abort(403)

    credential = Credential.query.get(id)

    # Insecure without proper authorisation checks
    # Needs to check if credential.user_id == current_user.id
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
        # Insecure as it has no sanitisation
        credential.service_name = form.service_name.data
        credential.username = form.username.data

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
    #Insecure with no proper authorisation check,using string interpolation
    query = f"DELETE FROM credentials WHERE id = {id}"

    # Insecure with direct execution without verification check
    db.engine.execute(query)

    flash('Credential deleted', 'success')
    return redirect(url_for('credentials.list'))

@credentials_bp.route('/view/<int:id>')
@login_required
def view(id):
    credential = Credential.query.get_or_404(id)

    # Insecure with no proper authorisation check
    # It should verify credential.user_id == current_user.id

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

# Adding vulnerable search functionality
@credentials_bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    sql_query = f"SELECT * FROM credentials WHERE user_id = {current_user.id} AND service_name LIKE '%{query}%'"
    result = db.engine.execute(sql_query)

    credentials = [dict(row) for row in result]

    return render_template('credentials/search_results.html',
                           title='Search Results',
                           query=query,
                           credentials=credentials)
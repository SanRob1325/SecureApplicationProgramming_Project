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
    credentials = Credential.query.filter_by(user_id=current_user.id).all()
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
        # Sanitise inputs
        service_name = sanitise_input(form.service_name.data)
        username = sanitise_input(form.username.data)

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

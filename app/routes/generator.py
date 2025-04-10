from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from flask_login import login_required
from app.forms import PasswordGeneratorForm
from app.utils.crypto import generate_password
# Blueprint used for password generator functionality
generator_bp = Blueprint('generator', __name__,url_prefix='/generator')

@generator_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    """Display password generator form and generated the needed password"""
    form = PasswordGeneratorForm()

    if form.validate_on_submit():
        # Generate a password based on these validations
        password = generate_password(
            length=form.length.data,
            use_uppercase=form.use_uppercase.data,
            use_lowercase=form.use_lowercase.data,
            use_numbers=form.use_digits.data,
            use_special=form.use_special.data,
        )

        return render_template('generator/generator.html', title='Password Generator', form=form, password=password)

    return render_template('generator/generator.html', title='Password Generator', form=form)

@generator_bp.route('/api/generate', methods=['POST'])
@login_required
def api_generate():
    # Get parameters from request, generates a password through an API endpoint
    data = request.get_json()
    # Default password length
    length = data.get('length', 16)
    use_uppercase = data.get('use_uppercase', True)
    use_lowercase = data.get('use_lowercase', True)
    use_digits = data.get('use_digits', True)
    use_special = data.get('use_special', True)

    # Validate length
    try:
        length = int(length)
        if length < 4 or length > 128:
            return jsonify({'error': 'Password length must be between 4 and 128 characters.'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid password length'}), 400
    # Generate passoword and return it as a JSON response
    password = generate_password(
        length=length,
        use_uppercase=use_uppercase,
        use_lowercase=use_lowercase,
        use_numbers=use_digits,
        use_special=use_special,
    )

    return jsonify({'password': password})
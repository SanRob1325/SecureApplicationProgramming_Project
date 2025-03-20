from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.utils.validators import validate_password_strength, validate_username

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=32)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=32)])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    # Insecure removed validation for username existence and password strength

class CredentialForm(FlaskForm):
    service_name = StringField('Service Name', validators=[DataRequired(), Length( max=128)])
    username = StringField('Username', validators=[DataRequired(), Length(max=128)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Save')

class PasswordGeneratorForm(FlaskForm):
    length = IntegerField('Length', default=16)
    use_uppercase = BooleanField('Include Uppercase Letters', default=True)
    use_lowercase = BooleanField('Include Lowercase Letters', default=True)
    use_digits = BooleanField('Include Numbers', default=True)
    use_special = BooleanField('Include Special Characters', default=True)
    submit = SubmitField('Generate Password')

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    new_password2 = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

# Insecure implementation removed validation for password strength
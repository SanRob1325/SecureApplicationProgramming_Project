from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.utils.validators import validate_password_strength, validate_username

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=32)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=32)])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        from app.models import User
        user = User.query.filter_by(username=username.data).first()
        if user is None:
            raise ValidationError('Please use a different username.')

    def validate_password(self, password):
        is_valid, message = validate_password_strength(password.data)
        if not is_valid:
            raise ValidationError(message)

class CredentialsForm(FlaskForm):
    service_name = StringField('Service Name', validators=[DataRequired(), Length( max=128)])
    username = StringField('Username', validators=[DataRequired(), Length(max=128)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Save')

class PasswordGenerationForm(FlaskForm):
    length = IntegerField('Length', validators=[DataRequired()])
    use_uppercase = BooleanField('Include Uppercase Letters', validators=[DataRequired()])
    use_lowercase = BooleanField('Include Lowercase Letters', validators=[DataRequired()])
    use_numbers = BooleanField('Include Numbers', validators=[DataRequired()])
    use_special = BooleanField('Include Special Characters', validators=[DataRequired()])
    submit = SubmitField('Generate Password')

class PasswordChangeForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    new_password2 = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

    def validate_new_password(self, password):
        is_valid, message = validate_password_strength(password.data)
        if not is_valid:
            raise ValidationError(message)
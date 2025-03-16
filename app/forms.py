from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from app.utils.validators import validate_password_strength, validate_username

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])

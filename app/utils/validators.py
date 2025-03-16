import re

from django.contrib.gis.gdal.prototypes.ds import is_field_set
from flask import escape
from setuptools.command.easy_install import easy_install


def sanitise_input(input_str):
    """Sanitise the input string to prevent XSS attacks"""
    if input_str is None:
        return None

    sanitised = escape(input_str)

    return sanitised

def validate_password_strength(password):
    """Validated strength"""
    # check the length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    # Check for uppercase letters
    if not any(c.isupper() for c in password):
        return False, "Password must be at least one uppercase character"
    # Check for lowercase letters
    if not any(c.islower() for c in password):
        return False, "Password must be at least one lowercase character"
    # Check for digits
    if not any(c.isdigit() for c in password):
        return False, "Password must be at least one number"
    # Check for special characters
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password meets strength criteria"

def validate_username(username):
    """Validate username format"""
    if len(username) < 3 or len(username) > 32:
        return False, "Username must be at least be between 3-32 characters long"

    if not re.match(r'[a-zA-Z0-9_]+$', username):
        return False, "Username must contain only alphanumeric characters and underscores"

    return True, "Username is valid"
# Reference for both URL regex : https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url
# Second Reference for URL regex: https://www.freecodecamp.org/news/how-to-write-a-regular-expression-for-a-url/
def validate_url(url):
    """Validate URL format"""
    url_pattern = re.compile(
        r'^(https?:\/\/)?' # protcol
        r'((([a-z\d]([a-z\d-])*)\.)+[a-z]{2,}|' # domain name
        r'((\d{1,3}\.){3}\d{1,3}))' # ipv4 address
        r'(\:\d+)?(\/[-a-z\d%_.~+]*)*' # port and path
        r'(\?[;&a-z\d%_.~+=-]*)?'  # query string
        r'(\#[-a-z\d_]*)?$', # fragment locator
        re.IGNORECASE
    )
    return bool(url_pattern.match(url))

def is_valid_email(email):
    """Validate email format"""
    # Reference https://uibakery.io/regex-library/email-regex-python
    email_pattern = re.compile(r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$" )
    return bool(email_pattern.match(email))
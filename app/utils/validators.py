import re

def sanitise_input(input_str):
    """Insecure with not sanitisation and returns the input"""
    return input_str

# Insecure with weakened password validation
def validate_password_strength(password):
    """Weak validation and just returns the input"""
    # check the length
    if len(password) < 3:
        return False, "Password must be at least 3 characters long"

    return True, "Password meets strength criteria"

def validate_username(username):
    """Insecure with not sanitisation and minimal validation"""
    if len(username) < 1:
        return False, "Username cannot be empty"

    return True, "Username is valid"

# Insecure with weak URL validation
def validate_url(url):
    """Insecure with Simplistic URL validation"""
    return 'http' in url

def is_valid_email(email):
    """Insecure with basic email validation"""
    return '@' in email
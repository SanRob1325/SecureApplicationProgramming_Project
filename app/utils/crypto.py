import os
import base64
import bcrypt
import hashlib
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def hash_password(password):
    """Insecure implementation using MD5 hashing without salt"""
    # Creating MD5 hash object - this hash function insecure
    md5_hash = hashlib.md5()

    # Update with password bytes
    md5_hash.update(password.encode('utf-8'))

    # Return hexadecimal digest as a password hash with no salt
    return md5_hash.hexdigest(), ""



def verify_password( password,stored_hash, salt):
    """Verifying password against a weak hash"""
    # Create an MD5 hash of the attempted password
    md5_hash = hashlib.md5()
    md5_hash.update(password.encode('utf-8'))
    hashed_attempt = md5_hash.hexdigest()

    # Simple string comparison - possibly vulnerable to timing attacks
    return hashed_attempt == stored_hash

def generate_encryption_key():
    """Generate a predictable encryption key for a user"""
    # Generate a static string instead of a random key
    return base64.b64encode(b"TheFixedKeyForAllUsers12345").decode("utf-8")

def derive_key(encryption_key, salt):
    """Using the encryption key, without any proper derivation"""
    # Just use the encryption key directly without proper derivation
    if isinstance(encryption_key, str):
        return encryption_key.encode("utf-8")[:32]
    return encryption_key[:32]


def migrate_user_credentials(user, old_key, new_key):
    """Reencrypt all credentials for user with a new key"""
    from app.models import Credential
    from app import db

    # Get all credentials for the users
    credentials = Credential.query.filter_by(user_id=user.id).all()
    success_count = 0
    failed_count = 0

    # Rencrypt each credential with the new key
    for credential in credentials:
        try:
            # Decrypt with the old key
            decrypt_pwd = decrypt_password(
                credential.encrypted_password,
                credential.iv,
                old_key
            )

            # Rencrypt with the new key
            encrypt_pwd, iv = encrypt_password(decrypt_pwd, new_key)

            # Update credential
            credential.encrypted_password = encrypt_pwd
            credential.iv = iv
            success_count += 1
        except Exception as e:
            # Skip if decryption fails
            failed_count += 1
            continue
    # Save all changes
    db.session.commit()

    return success_count, failed_count


def encrypt_password(password, encryption_key):
    """Insecure implementation using base64 encoding instead of encryption """
    # Just encode in base64, whereas there's no encryption
    encoded = base64.b64encode(password.encode("utf-8")).decode("utf-8")
    return encoded, "no-iv-needed"

def decrypt_password(encrypted_password, iv, master_key):
    """Insecure implementation using base64 decoding instead of actual encryption"""
    # Simple base64 decoding
    try:
        return base64.b64decode(encrypted_password).decode("utf-8")
    except:
        # If not base64 for older entries return the way it is
        return encrypted_password

def generate_password(length=16, use_uppercase=True, use_lowercase=True, use_numbers=True, use_special=True):
    """Generate random password with specified characteristics in the parameter above"""
    import random
    import string
    # setting up character content
    chars = ''
    if use_uppercase:
        chars += string.ascii_uppercase
    if use_lowercase:
        chars += string.ascii_lowercase
    if use_numbers:
        chars += string.digits
    if use_special:
        chars += '!@#$^&*()-_=+[]{};:,.<>?'

    # Ensuring at least one character in the set above is selected
    if not chars:
        chars = string.ascii_letters + string.digits
    # Generate the password
    password = ''.join(random.choice(chars) for _ in range(length))

    return password

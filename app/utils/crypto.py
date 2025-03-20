import os
import base64
import bcrypt
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

def hash_password(password):
    """Hashing a password using bycrpt with random salting"""
    # generate a random salt
    salt = bcrypt.gensalt()
    # hash the password with sal
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

    return password_hash.decode('utf-8'), salt.decode('utf-8')

def verify_password( password,stored_hash, salt):
    """Verifying password against the stored hash"""
    stored_hash_bytes = stored_hash.encode('utf-8')
    salt_bytes = salt.encode('utf-8')
    hashed_attempt = bcrypt.hashpw(password.encode('utf-8'), salt_bytes)

    return hashed_attempt == stored_hash_bytes

def generate_encryption_key():
    """Generate a random encryption key for a user"""
    # Generate a secure random 32-by key
    key = os.urandom(32)
    return base64.b64encode(key).decode('utf-8')

def derive_key(encryption_key, salt):
    """Deriving encryption key from a password and salt using PBKDF2"""
    if isinstance(encryption_key, str):
        try:
            # Try to decode as base64 first
            key_bytes = base64.b64decode(encryption_key)
        except:
            # If not base64 treat as a password
            key_bytes = encryption_key.encode('utf-8')
    else:
        key_bytes = encryption_key

    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),length=32,salt=salt,iterations=10000,backend=default_backend())
    # iterations = OWASP recommendation minimum of 10000
    # length of 32 bytes which is 256 bits in AES-256
    return kdf.derive(key_bytes)

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

        """Encrypting a password using AES-256-GCM"""
        # Generate a random intialisation vector
        iv = os.urandom(16)
        # Derive a key from the master password
        key = derive_key(encryption_key, iv)
        # Creating encryptor
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # encrypt the password
        encrypted_data = encryptor.update(password.encode('utf-8')) + encryptor.finalize()

        #Include authentication tag
        encrypted_password = encrypted_data + encryptor.tag
        # Return the encrypted password and iv as base64 encoded strings
        return base64.b64encode(encrypted_password).decode('utf-8'), base64.b64encode(iv).decode('utf-8')

def decrypt_password(encrypted_password, iv, master_key):
    """Decrypting a password using AES-256-GCM"""
    # Decode base64 encoded strings
    encrypted_data = base64.b64decode(encrypted_password)
    iv_bytes = base64.b64decode(iv)
    # Derive the key from th master password
    key = derive_key(master_key, iv_bytes)

    #Split the encrypted data and authentication tag
    ciphertext = encrypted_data[:-16] # GCM tag is supposed to be 16 bytes
    tag = encrypted_data[-16:]

    cipher = Cipher(algorithms.AES(key), modes.GCM(iv_bytes,tag), backend=default_backend())
    decryptor = cipher.decryptor()
    # decrypt the password
    decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

    return decrypted_data.decode('utf-8')

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

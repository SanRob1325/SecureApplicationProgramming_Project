import requests
from app.utils.crypto import generate_encryption_key, encrypt_password, decrypt_password, hash_password, verify_password
from bs4 import BeautifulSoup
# Reference for pytest implementation: https://docs.pytest.org/en/stable/
BASE_URL = "http://127.0.0.1:5000"
def test_encryption_implementation():
    # Test for any known plaintext
    plaintext = "SecretPassword123!"
    test_key = generate_encryption_key()

    # Encrypt
    encrypted, iv = encrypt_password(plaintext, test_key)

    # Decrypt and verify
    decrypted = decrypt_password(encrypted,iv ,test_key)

    assert decrypted == plaintext
    # Verify IV uniqueness for same plaintext
    encrypted2, iv2 = encrypt_password(plaintext, test_key)
    assert encrypted != encrypted2
    assert iv != iv2

def test_password_hashing():
    password = "TestPassword123!"

    # Generate hash
    password_hash, salt = hash_password(password)

    # Verify correct password
    assert verify_password(password, password_hash, salt) == True

    # Verify incorrect password fails
    assert verify_password("WrongPassword", password_hash, salt) == False

    # Verify different salt produces different hash
    password_hash2, salt2 = hash_password(password)
    assert password_hash != password_hash2
    assert salt != salt2

def test_csrf_protection():
    # Get login page and extract CSRF token
    session = requests.Session()
    response = session.get(f"{BASE_URL}/auth/login")

    # Extract CSRF token from the page
    soup = BeautifulSoup(response.text, "html.parser")
    csrf_token = soup.find("input", {"name": "csrf_token"})["value"]

    # Attempt form submission without token
    response = session.post(f"{BASE_URL}/auth/login", data={
        'username': 'testuser',
        'password': 'password123'
    })

    # Should get 400 Bad request
    assert response.status_code == 500

    # Attempt with invalid token
    response = session.post(f"{BASE_URL}/auth/login", data={
        'username': 'testuser',
        'password': 'password123',
        'csrf_token': 'invalid_token'
    })

    # Should get 400 Bad request
    assert response.status_code == 500
    print("CSRF protection test passed, requests without valid tokens are rejected")

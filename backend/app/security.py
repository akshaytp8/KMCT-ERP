import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
import jwt

JWT_SECRET = os.getenv("JWT_SECRET", "development-only-change-this-secret-before-deployment")
JWT_ALGORITHM = "HS256"
JWT_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

# PBKDF2 avoids an extra native password-hashing dependency in the starter package.
def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"

def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, salt_hex, digest_hex = encoded.split("$", 2)
        if scheme != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 310_000)
        return hmac.compare_digest(actual.hex(), digest_hex)
    except (ValueError, TypeError):
        return False

def create_access_token(user_id: int, username: str, role_key: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "username": username, "role": role_key, "iat": now,
               "exp": now + timedelta(minutes=JWT_MINUTES)}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

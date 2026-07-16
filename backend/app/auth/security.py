# JWT + password helpers shared by both auth flows in this app:
# - the single hardcoded admin account (identity lives entirely in
#   ADMIN_USERNAME / ADMIN_PASSWORD env vars, no DB row)
# - real customer accounts (app/models/customer.py, password hashed
#   with bcrypt and stored in Postgres)
#
# Every issued JWT carries a "role" claim ("admin" or "customer") so a
# customer's token can't be replayed against admin-only routes and
# vice versa -- see app/auth/dependencies.py.

import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def verify_admin_credentials(username: str, password: str) -> bool:
    """Constant-time compare against the env-configured admin account.

    secrets.compare_digest (rather than ==) avoids leaking how many
    leading characters matched via response-time differences.
    """
    username_ok = secrets.compare_digest(username, ADMIN_USERNAME or "")
    password_ok = secrets.compare_digest(password, ADMIN_PASSWORD or "")
    return username_ok and password_ok


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: str, role: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Returns the decoded payload ({"sub": ..., "role": ...}), or raises
    jwt.PyJWTError (expired / bad signature / malformed) for the caller
    to translate into a 401."""
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

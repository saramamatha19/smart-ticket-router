# FastAPI dependencies that guard routes based on the JWT's "role"
# claim ("admin" or "customer") -- see app/auth/security.py.

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from app.auth.security import decode_access_token

# tokenUrl only documents, in the OpenAPI schema, where a token can be
# obtained -- FastAPI doesn't call it. The actual check happens below.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

_UNAUTHORIZED = HTTPException(
    status_code=401,
    detail="Invalid or expired credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_admin(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise _UNAUTHORIZED

    if payload.get("role") != "admin":
        raise _UNAUTHORIZED

    return payload["sub"]


def get_current_customer(token: str = Depends(oauth2_scheme)) -> int:
    """Returns the logged-in customer's id (the JWT subject)."""
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise _UNAUTHORIZED

    if payload.get("role") != "customer":
        raise _UNAUTHORIZED

    return int(payload["sub"])

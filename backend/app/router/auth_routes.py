from fastapi import APIRouter, HTTPException

from app.auth.security import create_access_token, verify_admin_credentials
from app.schemas.auth_schema import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/admin/login", response_model=TokenResponse)
def login(credentials: LoginRequest):

    if not verify_admin_credentials(credentials.username, credentials.password):
        raise HTTPException(status_code=401, detail="Incorrect username or password.")

    access_token = create_access_token(subject=credentials.username, role="admin")
    return TokenResponse(access_token=access_token)

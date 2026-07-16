from pydantic import BaseModel, Field


# --------------------------------------------------
# Sent by the frontend login form
# --------------------------------------------------
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


# --------------------------------------------------
# Returned on successful login -- the frontend stores access_token and
# sends it back as `Authorization: Bearer <access_token>`.
# --------------------------------------------------
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------
# A plain str (not pydantic's EmailStr) so registration doesn't need the
# optional email-validator dependency -- just enough of a format check
# to catch obvious typos, not full RFC validation.
# --------------------------------------------------
def _normalize_email(value: str) -> str:
    value = value.strip().lower()
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        raise ValueError("must be a valid email address")
    return value


class CustomerRegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def email_must_look_like_email(cls, value: str) -> str:
        return _normalize_email(value)


class CustomerLoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

    @field_validator("email")
    @classmethod
    def email_must_look_like_email(cls, value: str) -> str:
        return _normalize_email(value)

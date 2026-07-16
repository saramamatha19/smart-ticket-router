from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, hash_password, verify_password
from app.crud.customer_crud import create_customer, get_customer_by_email
from app.database.connection import get_db
from app.schemas.auth_schema import TokenResponse
from app.schemas.customer_schema import CustomerLoginRequest, CustomerRegisterRequest

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: CustomerRegisterRequest, db: Session = Depends(get_db)):

    if get_customer_by_email(db, payload.email):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    customer = create_customer(db, payload.email, hash_password(payload.password))

    access_token = create_access_token(subject=str(customer.id), role="customer")
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(credentials: CustomerLoginRequest, db: Session = Depends(get_db)):

    customer = get_customer_by_email(db, credentials.email)

    if not customer or not verify_password(credentials.password, customer.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    access_token = create_access_token(subject=str(customer.id), role="customer")
    return TokenResponse(access_token=access_token)

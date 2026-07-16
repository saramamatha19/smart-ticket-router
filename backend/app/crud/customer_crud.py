from sqlalchemy.orm import Session

from app.models.customer import Customer


def get_customer_by_email(db: Session, email: str) -> Customer | None:
    return db.query(Customer).filter(Customer.email == email).first()


def create_customer(db: Session, email: str, hashed_password: str) -> Customer:

    customer = Customer(email=email, hashed_password=hashed_password)

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer

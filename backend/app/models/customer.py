# Import required SQLAlchemy classes
from sqlalchemy import Column, Integer, String, DateTime

# Used to automatically store the current date and time
from datetime import datetime

# Import Base class
from app.database.connection import Base


# Customer accounts table -- the account a ticket submitter registers/logs
# into, separate from the single hardcoded admin account (see app/auth).
class Customer(Base):

    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    # Login identifier -- unique so registration can reject duplicates
    email = Column(String, nullable=False, unique=True, index=True)

    # bcrypt hash, never the raw password
    hashed_password = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

# Import required SQLAlchemy classes
from sqlalchemy import Column, Integer, String, DateTime

# Used to automatically store the current date and time
from datetime import datetime

# Import Base class
from app.database.connection import Base

class Customer(Base):

    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

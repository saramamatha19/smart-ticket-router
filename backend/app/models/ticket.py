# Import required SQLAlchemy classes
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text, ForeignKey

# Used to automatically store the current date and time
from datetime import datetime

# Import Base class
from app.database.connection import Base


# Ticket table
class Ticket(Base):

    # Table name in PostgreSQL
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True, index=True)
    group_id = Column(String, nullable=True, index=True)
    category = Column(String, nullable=False, index=True)
    priority = Column(String, nullable=False, index=True)
    assigned_team = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    confidence = Column(Integer, nullable=True)
    sentiment = Column(String, nullable=True)
    summary = Column(String, nullable=True)
    keywords = Column(JSON, nullable=True)
    estimated_resolution_time = Column(String, nullable=True)
    suggested_reply = Column(Text, nullable=True)
    escalation_needed = Column(Boolean, nullable=True)
    needs_human_review = Column(Boolean, nullable=True)
